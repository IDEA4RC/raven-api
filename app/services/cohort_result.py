"""
Service for cohort result operations
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.cohort_result import CohortResult
from app.models.cohort import Cohort
from app.schemas.cohort_result import CohortResultCreate, CohortResultUpdate
from app.services.base import BaseService


class CohortResultService(BaseService[CohortResult, CohortResultCreate, CohortResultUpdate]):
    def __init__(self):
        super().__init__(CohortResult)

    def get_by_cohort_and_data_id(
        self, db: Session, *, cohort_id: int, data_id: List[str]
    ) -> Optional[CohortResult]:
        """
        Get a cohort result by cohort_id and data_id.
        """
        return (
            db.query(self.model)
            .filter(
                and_(
                    self.model.cohort_id == cohort_id,
                    self.model.data_id == data_id
                )
            )
            .first()
        )

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
        self, db: Session, *, obj_in: CohortResultCreate
    ) -> CohortResult:
        """
        Create a new cohort result.
        """
        # Verify that the cohort exists
        cohort = db.query(Cohort).filter(Cohort.id == obj_in.cohort_id).first()
        if not cohort:
            raise ValueError(f"Cohort with ID {obj_in.cohort_id} not found")

        # Check if this combination already exists
        existing = self.get_by_cohort_and_data_id(
            db, cohort_id=obj_in.cohort_id, data_id=obj_in.data_id
        )
        if existing:
            raise ValueError(
                f"CohortResult with cohort_id={obj_in.cohort_id} and data_id={obj_in.data_id} already exists"
            )

        db_obj = CohortResult(
            cohort_id=obj_in.cohort_id,
            data_id=obj_in.data_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_cohort_result(
        self, db: Session, *, cohort_id: int, data_id: List[str], obj_in: CohortResultUpdate
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
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete_cohort_result(
        self, db: Session, *, cohort_id: int, data_id: List[str]
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

    def delete_all_for_cohort(
        self, db: Session, *, cohort_id: int
    ) -> int:
        """
        Delete all cohort results for a specific cohort.
        Returns the number of deleted records.
        """
        # Verify that the cohort exists
        cohort = db.query(Cohort).filter(Cohort.id == cohort_id).first()
        if not cohort:
            raise ValueError(f"Cohort with ID {cohort_id} not found")

        deleted_count = (
            db.query(self.model)
            .filter(self.model.cohort_id == cohort_id)
            .delete()
        )
        db.commit()
        return deleted_count

    def get_data_ids_for_cohort(
        self, db: Session, *, cohort_id: int
    ) -> List[List[str]]:
        """
        Get all data_ids for a specific cohort.
        """
        results = (
            db.query(self.model.data_id)
            .filter(self.model.cohort_id == cohort_id)
            .all()
        )
        return [result[0] for result in results]

    def count_results_for_cohort(
        self, db: Session, *, cohort_id: int
    ) -> int:
        """
        Count the number of results for a specific cohort.
        """
        return (
            db.query(self.model)
            .filter(self.model.cohort_id == cohort_id)
            .count()
        )

    def bulk_create_for_cohort(
        self, db: Session, *, cohort_id: int, data_ids: List[List[str]]
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
            # Check if this combination already exists
            existing = self.get_by_cohort_and_data_id(
                db, cohort_id=cohort_id, data_id=data_id
            )
            if not existing:
                db_obj = CohortResult(
                    cohort_id=cohort_id,
                    data_id=data_id
                )
                db_objs.append(db_obj)

        if db_objs:
            db.add_all(db_objs)
            db.commit()
            for db_obj in db_objs:
                db.refresh(db_obj)

        return db_objs


# Create service instance
cohort_result_service = CohortResultService()