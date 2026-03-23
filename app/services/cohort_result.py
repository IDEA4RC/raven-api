"""
Service for cohort result operations
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging
import json
import re

from app.models.cohort_result import CohortResult
from app.models.cohort import Cohort
from app.models.analysis import Analysis
from app.models.metadata_search import MetadataSearch
from app.schemas.cohort_result import CohortResultCreate, CohortResultUpdate
from app.services.base import BaseService
from app.services.vantage_6 import vantage6_service
from app.utils.constants import CohortStatus, typeOfDiseases


logger = logging.getLogger(__name__)


class CohortResultService(
    BaseService[CohortResult, CohortResultCreate, CohortResultUpdate]
):
    def __init__(self):
        super().__init__(CohortResult)

    def _normalize_patient_ids(self, value: object) -> List[str]:
        """Normalize patient IDs coming from DB rows or serialized JSON-like payloads."""
        if value is None:
            return []

        if isinstance(value, list):
            patient_ids: List[str] = []
            for item in value:
                patient_ids.extend(self._normalize_patient_ids(item))
            return patient_ids

        if isinstance(value, str):
            raw_value = value.strip()
            if not raw_value:
                return []

            if raw_value.startswith("[") and raw_value.endswith("]"):
                try:
                    decoded = json.loads(raw_value)
                    return self._normalize_patient_ids(decoded)
                except json.JSONDecodeError:
                    pass

            normalized = raw_value.strip('"').strip("'")
            return [normalized] if normalized else []

        normalized = str(value).strip().strip('"').strip("'")
        return [normalized] if normalized else []

    def _normalize_data_ids_to_ints(self, value: object) -> List[int]:
        """Normalize incoming data_id payloads into a flat list of integers."""
        if value is None:
            return []

        if isinstance(value, int):
            return [value]

        if isinstance(value, (list, tuple, set)):
            numbers: List[int] = []
            for item in value:
                numbers.extend(self._normalize_data_ids_to_ints(item))
            return numbers

        if isinstance(value, str):
            raw_value = value.strip()
            if not raw_value:
                return []

            if (raw_value.startswith("[") and raw_value.endswith("]")) or (
                raw_value.startswith("{") and raw_value.endswith("}")
            ):
                try:
                    decoded = json.loads(raw_value)
                    return self._normalize_data_ids_to_ints(decoded)
                except json.JSONDecodeError:
                    pass

            return [int(n) for n in re.findall(r"\d+", raw_value)]

        return self._normalize_data_ids_to_ints(str(value))

    def _collect_patient_ids_for_cohort(
        self, db: Session, *, cohort_id: int
    ) -> List[int]:
        cohort_result = (
            db.query(CohortResult).filter(CohortResult.cohort_id == cohort_id).first()
        )

        return cohort_result.data_id

    def _update_cohort_execution_and_v6(
        self,
        db: Session,
        *,
        cohort: Cohort,
        access_token: str,
    ) -> None:
        # Persist EXECUTED status as soon as cohort results have been stored.
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

        patient_ids = self._collect_patient_ids_for_cohort(db, cohort_id=cohort.id)
        logger.info(
            "Collected %d patient IDs for cohort_id=%s patient list=%s",
            len(patient_ids),
            cohort.id,
            patient_ids,
        )

        if not patient_ids:
            raise ValueError(
                f"No patient IDs found in cohort results for cohort {cohort.id}"
            )

        logger.info(
            "[V6] Creating cohort dataframe for cohort_id=%s session_id=%s",
            cohort.id,
            analysis.session_id_vantage,
        )

        dataframe_id = vantage6_service.create_new_cohort(
            access_token=access_token,
            session_id=analysis.session_id_vantage,
            features=features,
            patient_ids=patient_ids,
        )

        if dataframe_id in (None, -1):
            raise RuntimeError("Failed to create cohort in Vantage6")

        cohort.dataframe_vantage_id = dataframe_id

        db.add(cohort)
        db.commit()
        db.refresh(cohort)

    def get_by_cohort_and_data_id(
        self, db: Session, *, cohort_id: int, data_id: List[int]
    ) -> Optional[CohortResult]:
        """
        Get a cohort result by cohort_id and data_id.
        """
        return (
            db.query(self.model)
            .filter(
                and_(self.model.cohort_id == cohort_id, self.model.data_id == data_id)
            )
            .first()
        )

    def get_by_cohort_last(self, db: Session, *, cohort_id: int) -> CohortResult:
        """
        Get the last cohort result for a specific cohort.
        """
        return db.query(self.model).filter(self.model.cohort_id == cohort_id).first()

    def get_by_cohort(
        self, db: Session, *, cohort_id: int, skip: int = 0, limit: int = 100
    ) -> List[CohortResult]:
        """
        Get all cohort results for a specific cohort.
        """
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
        """
        Create a new cohort result.
        """
        # Verify that the cohort exists
        cohort = db.query(Cohort).filter(Cohort.id == obj_in.cohort_id).first()
        if not cohort:
            raise ValueError(f"Cohort with ID {obj_in.cohort_id} not found")

        # Upsert: overwrite existing data_id if a record already exists for this cohort.
        existing = self.get_by_cohort_last(db, cohort_id=obj_in.cohort_id)

        normalized_data_ids = list(
            dict.fromkeys(self._normalize_data_ids_to_ints(obj_in.data_id))
        )
        if not normalized_data_ids:
            raise ValueError("data_id must contain at least one integer value")

        if existing:
            existing.data_id = normalized_data_ids
            db.add(existing)
            db.commit()
            db.refresh(existing)
            db_obj = existing
        else:
            db_obj = CohortResult(
                cohort_id=obj_in.cohort_id, data_id=normalized_data_ids
            )
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)

        logger.info(
            "Cohort result created/updated with ID %s for cohort_id=%s ",
            db_obj.id,
            obj_in.cohort_id,
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
        data_id: List[int],
        obj_in: CohortResultUpdate,
    ) -> CohortResult:
        """
        Update a cohort result by cohort_id and data_id.
        """
        db_obj = self.get_by_cohort_and_data_id(
            db, cohort_id=cohort_id, data_id=data_id
        )
        if not db_obj:
            raise ValueError(
                f"CohortResult with cohort_id={cohort_id} and data_id={data_id} not found"
            )

        update_data = obj_in.model_dump(exclude_unset=True)

        if "data_id" in update_data and update_data["data_id"] is not None:
            normalized_data_ids = list(
                dict.fromkeys(self._normalize_data_ids_to_ints(update_data["data_id"]))
            )
            if not normalized_data_ids:
                raise ValueError("data_id must contain at least one integer value")
            update_data["data_id"] = normalized_data_ids

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete_cohort_result(
        self, db: Session, *, cohort_id: int, data_id: List[int]
    ) -> bool:
        """
        Delete a cohort result by cohort_id and data_id.
        """
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
        """
        Delete all cohort results for a specific cohort.
        Returns the number of deleted records.
        """
        # Verify that the cohort exists
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
    ) -> List[List[int]]:
        """
        Get all data_ids for a specific cohort.
        """
        results = (
            db.query(self.model.data_id).filter(self.model.cohort_id == cohort_id).all()
        )
        return [
            list(dict.fromkeys(self._normalize_data_ids_to_ints(result[0])))
            for result in results
        ]

    def count_results_for_cohort(self, db: Session, *, cohort_id: int) -> int:
        """
        Count the number of results for a specific cohort.
        """
        return db.query(self.model).filter(self.model.cohort_id == cohort_id).count()

    def bulk_create_for_cohort(
        self,
        db: Session,
        *,
        cohort_id: int,
        data_ids: List[List[int]],
        access_token: str,
    ) -> List[CohortResult]:
        """
        Create multiple cohort results for a cohort in a single transaction.
        """
        # Verify that the cohort exists
        cohort = db.query(Cohort).filter(Cohort.id == cohort_id).first()
        if not cohort:
            raise ValueError(f"Cohort with ID {cohort_id} not found")

        # Create all the objects
        db_objs = []
        for data_id in data_ids:
            normalized_data_ids = list(
                dict.fromkeys(self._normalize_data_ids_to_ints(data_id))
            )
            if not normalized_data_ids:
                continue

            # Check if this combination already exists
            existing = self.get_by_cohort_and_data_id(
                db, cohort_id=cohort_id, data_id=normalized_data_ids
            )
            if not existing:
                db_obj = CohortResult(cohort_id=cohort_id, data_id=normalized_data_ids)
                db_objs.append(db_obj)

        if db_objs:
            db.add_all(db_objs)
            db.commit()
            for db_obj in db_objs:
                db.refresh(db_obj)

            self._update_cohort_execution_and_v6(
                db,
                cohort=cohort,
                access_token=access_token,
            )

        return db_objs


# Create service instance
cohort_result_service = CohortResultService()
