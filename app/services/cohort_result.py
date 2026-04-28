"""
Service for cohort result operations
"""

from typing import Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from app.models.cohort_result import CohortResult
from app.models.cohort import Cohort
from app.models.analysis import Analysis
from app.models.metadata_search import MetadataSearch
from app.models.workspace import Workspace
from app.schemas.cohort_result import CohortResultCreate, CohortResultUpdate
from app.services.base import BaseService
from app.services.vantage_6 import vantage6_service
from app.utils.constants import CohortStatus, typeOfDiseases, COE_TOKEN_MAP, COE_TOKEN_ORG_MAP


logger = logging.getLogger(__name__)


class CohortResultService(
    BaseService[CohortResult, CohortResultCreate, CohortResultUpdate]
):
    def __init__(self):
        super().__init__(CohortResult)

    def _collect_patient_ids_from_jsonb(self, executions: list) -> List[int]:
        ids: List[int] = []
        for entry in (executions or []):
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

        workspace = db.query(Workspace).filter(Workspace.id == cohort.workspace_id).first()
        study_id = workspace.v6_study_id if workspace else None

        createDataFrameResponse = vantage6_service.create_new_cohort(
            access_token=access_token,
            session_id=analysis.session_id_vantage,
            features=features,
            patient_ids_by_org=patient_ids_by_org,
            study_id=study_id,
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

    def get_by_cohort_last(self, db: Session, *, cohort_id: int) -> Optional[CohortResult]:
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

    def create_for_cohort(
        self, db: Session, *, obj_in: CohortResultCreate, access_token: str
    ) -> CohortResult:
        cohort = db.query(Cohort).filter(Cohort.id == obj_in.cohort_id).first()
        if not cohort:
            raise ValueError(f"Cohort with ID {obj_in.cohort_id} not found")

        if len(obj_in.data_id) != 1:
            raise ValueError("data_id must contain exactly one CoE token key")

        token, entries = next(iter(obj_in.data_id.items()))
        center = COE_TOKEN_MAP.get(token)
        if center is None:
            raise ValueError(f"Unknown CoE token: {token}")

        new_executions = [
            {
                "token": token,
                "center": center,
                "execution_date": e.execution_date,
                "patient_ids": e.patient_ids,
            }
            for e in entries
        ]

        existing = self.get_by_cohort_last(db, cohort_id=obj_in.cohort_id)
        if existing:
            current = existing.data_id or []
            existing.data_id = current + new_executions
            db.add(existing)
            db.commit()
            db.refresh(existing)
            db_obj = existing
        else:
            db_obj = CohortResult(cohort_id=obj_in.cohort_id, data_id=new_executions)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)

        logger.info(
            "Cohort result appended for cohort_id=%s center=%s executions=%d total_stored=%d",
            obj_in.cohort_id,
            center,
            len(new_executions),
            len(db_obj.data_id),
        )

        self._update_cohort_execution_and_v6(
            db,
            cohort=cohort,
            access_token=access_token,
        )

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

    def get_data_ids_for_cohort(
        self, db: Session, *, cohort_id: int
    ) -> List[Any]:
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
