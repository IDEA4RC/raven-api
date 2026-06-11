"""
Service for cohort result operations
"""

from typing import Any, List, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timezone
import logging

from app.models.cohort_result import CohortResult
from app.models.cohort import Cohort
from app.models.analysis import Analysis
from app.models.algorithm import Algorithm
from app.models.cohort_algorithm import CohortAlgorithm
from app.models.metadata_search import MetadataSearch
from app.models.permit import Permit
from app.models.workspace import Workspace
from app.schemas.cohort_result import CohortResultCreate, CohortResultUpdate
from app.services.base import BaseService
from app.services.vantage_6 import vantage6_service
from app.utils.constants import (
    CohortStatus,
    typeOfDiseases,
    COE_TOKEN_MAP,
    COE_TOKEN_ORG_MAP,
    PermitStatus,
)
from app.utils.metrics_logger import log_event

logger = logging.getLogger(__name__)


class CohortResultService(
    BaseService[CohortResult, CohortResultCreate, CohortResultUpdate]
):
    def __init__(self):
        super().__init__(CohortResult)

    def _get_expected_coes(self, db: Session, cohort: Cohort) -> Set[str]:
        """Get COE center names expected from the granted permit for this workspace."""
        permit = (
            db.query(Permit)
            .filter(
                Permit.workspace_id == cohort.workspace_id,
                Permit.status == PermitStatus.GRANTED,
            )
            .first()
        )
        if not permit or not permit.coes_granted:
            return set()
        return set(permit.coes_granted)

    def _get_responded_coes(self, data_id: list) -> Set[str]:
        """Get COE center names that have already sent results, derived from token."""
        return {
            COE_TOKEN_MAP[entry["token"]]
            for entry in (data_id or [])
            if entry.get("token") and entry["token"] in COE_TOKEN_MAP
        }

    def _delete_all_analyses_for_cohort(self, db: Session, cohort_id: int) -> None:
        """Delete all algorithms (all types) associated with this cohort."""
        cohort_algorithm_rows = (
            db.query(CohortAlgorithm)
            .filter(CohortAlgorithm.cohort_id == cohort_id)
            .all()
        )
        algorithm_ids = [row.algorithm_id for row in cohort_algorithm_rows]

        db.query(CohortAlgorithm).filter(
            CohortAlgorithm.cohort_id == cohort_id
        ).delete()

        for alg_id in algorithm_ids:
            still_linked = (
                db.query(CohortAlgorithm)
                .filter(CohortAlgorithm.algorithm_id == alg_id)
                .count()
            )
            if still_linked == 0:
                db.query(Algorithm).filter(Algorithm.id == alg_id).delete()

        db.commit()
        logger.info(
            "[CREATE_COHORT_RESULT] Deleted all analyses for cohort_id=%s (count=%d)",
            cohort_id,
            len(algorithm_ids),
        )

    def _collect_patient_ids_from_jsonb(self, executions: list) -> List[int]:
        ids: List[int] = []
        for entry in executions or []:
            ids.extend(entry.get("patient_ids", []))
        return list(dict.fromkeys(ids))

    def _collect_patient_ids_for_cohort(
        self, db: Session, *, cohort_id: int
    ) -> List[int]:
        cohort_result = (
            db.query(CohortResult).filter(CohortResult.cohort_id == cohort_id).first()
        )
        if not cohort_result or not cohort_result.data_id:
            return []
        return self._collect_patient_ids_from_jsonb(cohort_result.data_id)

    def _collect_patient_ids_by_org(
        self, db: Session, *, cohort_id: int
    ) -> dict[int, List[int]]:
        """Build {v6_org_id: [patient_ids]} from stored executions.
        Only includes centers that have a V6 node in COE_TOKEN_ORG_MAP.
        Multiple executions from the same center are merged and deduplicated.
        """
        cohort_result = (
            db.query(CohortResult).filter(CohortResult.cohort_id == cohort_id).first()
        )
        if not cohort_result or not cohort_result.data_id:
            return {}

        org_patient_ids: dict[int, List[int]] = {}
        for entry in cohort_result.data_id:
            token = entry.get("token")
            org_id = COE_TOKEN_ORG_MAP.get(token)
            if org_id is None:
                continue
            existing = org_patient_ids.get(org_id, [])
            all_ids = existing + entry.get("patient_ids", [])
            org_patient_ids[org_id] = list(dict.fromkeys(all_ids))

        logger.info(
            "[COLLECT_PATIENT_IDS_BY_ORG] For cohort_id=%s collected patient IDs by org: %s",
            cohort_id,
            {org_id: len(ids) for org_id, ids in org_patient_ids.items()},
        )
        return org_patient_ids

    def _update_cohort_execution_and_v6(
        self,
        db: Session,
        *,
        cohort: Cohort,
        access_token: str,
    ) -> None:
        cohort.status = CohortStatus.EXECUTED.value
        db.add(cohort)
        db.commit()
        db.refresh(cohort)

        analysis = db.query(Analysis).filter(Analysis.id == cohort.analysis_id).first()
        if not analysis:
            raise ValueError(
                f"Analysis {cohort.analysis_id} not found for cohort {cohort.id}"
            )

        if not analysis.session_id_vantage:
            raise ValueError(
                f"Analysis {analysis.id} does not have a Vantage6 session ID"
            )

        metadata = (
            db.query(MetadataSearch)
            .filter(MetadataSearch.workspace_id == cohort.workspace_id)
            .first()
        )
        if not metadata:
            raise ValueError(f"Metadata for workspace {cohort.workspace_id} not found")

        features = metadata.type_cancer
        if features == "H&N":
            features = typeOfDiseases.HAndN.value
        elif features.lower() == "sarc":
            features = typeOfDiseases.SARCOMA.value

        patient_ids_by_org = self._collect_patient_ids_by_org(db, cohort_id=cohort.id)
        logger.info(
            "Collected patient IDs by org for cohort_id=%s: %s",
            cohort.id,
            {org_id: len(ids) for org_id, ids in patient_ids_by_org.items()},
        )

        if not patient_ids_by_org:
            raise ValueError(
                f"No patient IDs with a V6 node found in cohort results for cohort {cohort.id}"
            )

        logger.info(
            "[V6] Creating cohort dataframe for cohort_id=%s session_id=%s",
            cohort.id,
            analysis.session_id_vantage,
        )

        workspace = (
            db.query(Workspace).filter(Workspace.id == cohort.workspace_id).first()
        )
        # study_id = workspace.v6_study_id if workspace else None

        createDataFrameResponse = vantage6_service.create_new_cohort(
            db=db,
            access_token=access_token,
            session_id=analysis.session_id_vantage,
            features=features,
            patient_ids_by_org=patient_ids_by_org,
            workspace_id=workspace.id,
        )

        if createDataFrameResponse.dataframe_id in (None, -1):
            raise RuntimeError("Failed to create cohort in Vantage6")

        cohort.dataframe_vantage_id = createDataFrameResponse.dataframe_id
        cohort.task_id_vantage = createDataFrameResponse.task_id

        db.add(cohort)
        db.commit()
        db.refresh(cohort)

    def get_by_cohort_and_data_id(
        self, db: Session, *, cohort_id: int, data_id: list
    ) -> Optional[CohortResult]:
        return (
            db.query(self.model)
            .filter(
                and_(self.model.cohort_id == cohort_id, self.model.data_id == data_id)
            )
            .first()
        )

    def get_by_cohort_last(
        self, db: Session, *, cohort_id: int
    ) -> Optional[CohortResult]:
        return db.query(self.model).filter(self.model.cohort_id == cohort_id).first()

    def get_by_cohort(
        self, db: Session, *, cohort_id: int, skip: int = 0, limit: int = 100
    ) -> List[CohortResult]:
        return (
            db.query(self.model)
            .filter(self.model.cohort_id == cohort_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def _maybe_create_dataframe(
        self,
        db: Session,
        *,
        cohort: Cohort,
        data_id: list,
        access_token: str,
    ) -> None:
        """Create the V6 dataframe if all expected COEs have responded."""
        expected_coes = self._get_expected_coes(db, cohort)
        responded_coes = self._get_responded_coes(data_id)

        logger.info(
            "[CREATE_COHORT_RESULT] COE status — expected: %s | responded: %s",
            expected_coes,
            responded_coes,
        )

        if expected_coes and responded_coes >= expected_coes:
            logger.info(
                "[CREATE_COHORT_RESULT] All expected COEs responded — creating dataframe"
            )
            self._update_cohort_execution_and_v6(
                db, cohort=cohort, access_token=access_token
            )
            return

        logger.info(
            "[CREATE_COHORT_RESULT] Waiting for more COEs — %d/%d responded",
            len(responded_coes),
            len(expected_coes) if expected_coes else "?",
        )

    def create_for_cohort(
        self, db: Session, *, obj_in: CohortResultCreate, access_token: str
    ) -> Optional[CohortResult]:
        # logger.info(
        #     "[CREATE_COHORT_RESULT] START - full payload: %s", obj_in.model_dump()
        # )

        cohort = db.query(Cohort).filter(Cohort.id == obj_in.cohort_id).first()
        if not cohort:
            logger.error("[CREATE_COHORT_RESULT] Cohort %s not found", obj_in.cohort_id)
            raise ValueError(f"Cohort with ID {obj_in.cohort_id} not found")

        if len(obj_in.data_id) != 1:
            # logger.error(
            #     "[CREATE_COHORT_RESULT] data_id has %d keys, expected 1: %s",
            #     len(obj_in.data_id),
            #     list(obj_in.data_id.keys()),
            # )
            raise ValueError("data_id must contain exactly one CoE token key")

        token, entries = next(iter(obj_in.data_id.items()))
        # logger.info(
        #     "[CREATE_COHORT_RESULT] Token received: %s | entries count: %d",
        #     token,
        #     len(entries),
        # )

        center = COE_TOKEN_MAP.get(token)
        if center is None:
            logger.error(
                "[CREATE_COHORT_RESULT] Unknown CoE token: '%s'",
                token,
            )
            raise ValueError(f"Unknown CoE token: {token}")

        metadata = (
            db.query(MetadataSearch)
            .filter(MetadataSearch.workspace_id == cohort.workspace_id)
            .first()
        )
        disease_type = metadata.type_cancer if metadata else None
        expected_coes = self._get_expected_coes(db, cohort)
        if expected_coes and center not in expected_coes:
            logger.warning(
                "[CREATE_COHORT_RESULT] Center '%s' not in coes_granted %s — rejecting",
                center,
                expected_coes,
            )

            log_event(
                "coe_result",
                "ignored",
                center=center,
                cohort_id=obj_in.cohort_id,
                workspace_id=cohort.workspace_id,
            )

            return None

        # Reject if this token already submitted (prevents duplicates on re-execution)
        # existing_check = self.get_by_cohort_last(db, cohort_id=obj_in.cohort_id)
        # already_submitted = existing_check and any(
        #     e.get("token") == token for e in (existing_check.data_id or [])
        # )
        # if already_submitted:
        #     logger.warning(
        #         "[CREATE_COHORT_RESULT] Token '%s' already submitted for cohort %s — rejecting duplicate",
        #         token,
        #         cohort.id,
        #     )
        #     raise ValueError(
        #         f"Token '{token}' has already submitted results for this cohort"
        #     )

        # for i, e in enumerate(entries):
        #     logger.info(
        #         "[CREATE_COHORT_RESULT] Entry[%d] execution_date=%s patient_ids count=%d ",
        #         i,
        #         e.execution_date,
        #         len(e.patient_ids),
        #     )

        now_utc = datetime.now(timezone.utc)
        now_iso = now_utc.isoformat()
        new_executions = [
            {
                "token": token,
                "execution_date": e.execution_date,
                "patient_ids": e.patient_ids,
                "received_at": now_iso,
            }
            for e in entries
        ]

        total_patients = sum(len(e.patient_ids) for e in entries)
        log_event(
            "coe_result",
            "received",
            center=center,
            cohort_id=obj_in.cohort_id,
            cohort_size=total_patients,
            workspace_id=cohort.workspace_id,
            disease_type=disease_type,
        )

        existing = self.get_by_cohort_last(db, cohort_id=obj_in.cohort_id)
        if existing:
            current = existing.data_id or []
            filtered = [e for e in current if e.get("token") != token]

            logger.info(
                "[CREATE_COHORT_RESULT] Replacing data for token '%s' in record id=%s",
                token,
                existing.id,
            )

            # upsert lógico: reemplazar por las nuevas ejecuciones
            existing.data_id = filtered + new_executions

            db.add(existing)
            db.commit()
            db.refresh(existing)
            db_obj = existing
        else:
            logger.info("[CREATE_COHORT_RESULT] Creating new CohortResult record")
            db_obj = CohortResult(cohort_id=obj_in.cohort_id, data_id=new_executions)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)

        total_entries = len(db_obj.data_id or [])

        if total_entries == 0:
            #  no ha llegado nada válido → seguimos en RUNNING
            logger.info("[STATUS] No valid data yet → keeping RUNNING")
            cohort.status = CohortStatus.RUNNING.value

        else:

            tokens_present = {e["token"] for e in db_obj.data_id}

            logger.info(
                "[CREATE_COHORT_RESULT] Total entries for cohort_id=%s: %d | Expected CoEs: %s | Tokens present: %s",
                obj_in.cohort_id,
                total_entries,
                expected_coes,
                tokens_present,
            )

            if expected_coes and len(tokens_present) >= len(expected_coes):
                logger.info("[STATUS] All expected CoEs responded → COMPLETED")
                cohort.status = CohortStatus.EXECUTED.value
                log_event(
                    "cohort",
                    "status_change",
                    cohort_id=obj_in.cohort_id,
                    workspace_id=cohort.workspace_id,
                    disease_type=disease_type,
                    message="EXECUTED — all COEs responded",
                )
            else:
                expected_count = len(expected_coes) if expected_coes else 0

                logger.info("[STATUS] Partial data received → PARTIAL")
                cohort.status = CohortStatus.PARTIALLY_EXECUTED.value
                log_event(
                    "cohort",
                    "status_change",
                    cohort_id=obj_in.cohort_id,
                    workspace_id=cohort.workspace_id,
                    disease_type=disease_type,
                    message=f"PARTIALLY_EXECUTED — {len(tokens_present)}/{expected_count} COEs responded",
                )

        db.add(cohort)
        db.commit()
        logger.info(
            "[CREATE_COHORT_RESULT] Saved OK cohort_id=%s token=%s executions=%d total_stored=%d",
            obj_in.cohort_id,
            token,
            len(new_executions),
            len(db_obj.data_id),
        )
        self._maybe_create_dataframe(
            db, cohort=cohort, data_id=db_obj.data_id, access_token=access_token
        )
        logger.info("[CREATE_COHORT_RESULT] END OK cohort_id=%s", obj_in.cohort_id)

        return db_obj

    def update_cohort_result(
        self,
        db: Session,
        *,
        cohort_id: int,
        data_id: list,
        obj_in: CohortResultUpdate,
    ) -> CohortResult:
        db_obj = self.get_by_cohort_and_data_id(
            db, cohort_id=cohort_id, data_id=data_id
        )
        if not db_obj:
            raise ValueError(
                f"CohortResult with cohort_id={cohort_id} and data_id={data_id} not found"
            )

        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete_cohort_result(
        self, db: Session, *, cohort_id: int, data_id: list
    ) -> bool:
        db_obj = self.get_by_cohort_and_data_id(
            db, cohort_id=cohort_id, data_id=data_id
        )
        if not db_obj:
            raise ValueError(
                f"CohortResult with cohort_id={cohort_id} and data_id={data_id} not found"
            )

        db.delete(db_obj)
        db.commit()
        return True

    def delete_all_for_cohort(self, db: Session, *, cohort_id: int) -> int:
        cohort = db.query(Cohort).filter(Cohort.id == cohort_id).first()
        if not cohort:
            raise ValueError(f"Cohort with ID {cohort_id} not found")

        deleted_count = (
            db.query(self.model).filter(self.model.cohort_id == cohort_id).delete()
        )
        db.commit()
        return deleted_count

    def get_data_ids_for_cohort(self, db: Session, *, cohort_id: int) -> List[Any]:
        results = (
            db.query(self.model.data_id).filter(self.model.cohort_id == cohort_id).all()
        )
        return [result[0] for result in results]

    def count_results_for_cohort(self, db: Session, *, cohort_id: int) -> int:
        return db.query(self.model).filter(self.model.cohort_id == cohort_id).count()

    def bulk_create_for_cohort(
        self,
        db: Session,
        *,
        cohort_id: int,
        data_ids: list,
        access_token: str,
    ) -> List[CohortResult]:
        raise NotImplementedError(
            "bulk_create_for_cohort is not supported with the new CoE token format"
        )


# Create service instance
cohort_result_service = CohortResultService()
