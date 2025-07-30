"""
Service for handling cohort operations in the application.
"""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.cohort import Cohort
from app.models.workspace import Workspace
from app.models.workspace_history import WorkspaceHistory
from app.schemas.cohort import Cohort, CohortCreate, CohortUpdate, CohortStatusUpdate
from app.services.base import BaseService
from app.utils.constants import CohortStatus


class CohortService(BaseService[Cohort, CohortCreate, CohortUpdate]):

    def create_with_history(
        self, db: Session, obj_in: CohortCreate, user_id: int
    ) -> Cohort:
        """
        Create a new cohort and log the creation in the workspace history.
        """

        # Check if the workspace exists
        workspace = db.query(Workspace).filter(Workspace.id == obj_in.workspace_id).first()
        if not workspace:
            raise ValueError(f"Workspace {obj_in.workspace_id} not found")
        
        # Create the cohort
        obj_in_data = obj_in.model_dump()
        if not obj_in_data.get("creation_date"):
            obj_in_data["creation_date"] = datetime.now(timezone.utc)
        db_obj = Cohort(**obj_in_data)
        db.add(db_obj)
        db.commit()

        # Log the creation in the workspace history
        workspace = db.query(Workspace).filter(Workspace.id == obj_in.workspace_id).first()
        if workspace:
            history_entry = WorkspaceHistory(
                workspace_id=workspace.id,
                action="Cohort Created",
                phase="Data Analysis",
                creator_id=user_id,
                date=datetime.now(timezone.utc),
                description=f"Cohort {db_obj.id} created."
            )
            db.add(history_entry)
            db.commit()

        return db_obj

    def get_all_cohorts(self, db: Session, skip: int = 0, limit: int = 100) -> List[Cohort]:
        """
        Get all cohorts with pagination.
        """
        return db.query(Cohort).offset(skip).limit(limit).all()

    def get_cohorts_by_workspace(self, db: Session, workspace_id: int) -> List[Cohort]:
        """
        Get all cohorts for a specific workspace.
        """
        return db.query(Cohort).filter(Cohort.workspace_id == workspace_id).all()
    
    def update_cohort_status(
        self, db: Session, obj_in: CohortStatusUpdate, cohort_id: int, user_id: int
    ) -> Cohort:
        """
        Update the status of a cohort and log the change in workspace history.
        """
        cohort = db.query(Cohort).filter(Cohort.id == cohort_id).first()
        if not cohort:
            raise ValueError(f"Cohort {cohort_id} not found")

        # Update the cohort status
        obj_in_data = obj_in.model_dump()
        cohort.status = obj_in_data.get("status", cohort.status)
        if not obj_in_data.get("update_date"):
            cohort.update_date = datetime.now(timezone.utc)
        db.add(cohort)
        db.commit()

        # Log the status change in the workspace history
        workspace = db.query(Workspace).filter(Workspace.id == cohort.workspace_id).first()
        if workspace:
            history_entry = WorkspaceHistory(
                workspace_id=workspace.id,
                action="Cohort Status Updated",
                phase="Data Analysis",
                creator_id=user_id,
                date=datetime.now(timezone.utc),
                description=f"Cohort {cohort.id} status updated to {cohort.status}."
            )
            db.add(history_entry)
            db.commit()
        else:
            raise ValueError(f"Workspace {cohort.workspace_id} not found for cohort {cohort_id}")

        return cohort
    
    def update_cohort(
        self, db: Session, obj_in: CohortUpdate, cohort_id: int, user_id: int
    ) -> Cohort:
        """
        Update a cohort and log the change in workspace history.
        """
        cohort = db.query(Cohort).filter(Cohort.id == cohort_id).first()
        if not cohort:
            raise ValueError(f"Cohort {cohort_id} not found")

        # Update the cohort fields
        for field, value in obj_in.model_dump(exclude_unset=True).items():
            setattr(cohort, field, value)
        
        if not obj_in.update_date:
            cohort.update_date = datetime.now(timezone.utc)
        
        db.add(cohort)
        db.commit()

        # Log the update in the workspace history
        workspace = db.query(Workspace).filter(Workspace.id == cohort.workspace_id).first()
        if workspace:
            history_entry = WorkspaceHistory(
                workspace_id=workspace.id,
                action="Cohort Updated",
                phase="Data Analysis",
                creator_id=user_id,
                date=datetime.now(timezone.utc),
                description=f"Cohort {cohort.id} updated."
            )
            db.add(history_entry)
            db.commit()
        else:
            raise ValueError(f"Workspace {cohort.workspace_id} not found for cohort {cohort_id}")

        return cohort
    
    def delete_cohort(
        self, db: Session, cohort_id: int, user_id: int
    ) -> None:
        """
        Delete a cohort and log the deletion in the workspace history.
        """
        cohort = db.query(Cohort).filter(Cohort.id == cohort_id).first()
        if not cohort:
            raise ValueError(f"Cohort {cohort_id} not found")

        db.delete(cohort)
        db.commit()

        # Log the deletion in the workspace history
        workspace = db.query(Workspace).filter(Workspace.id == cohort.workspace_id).first()
        if workspace:
            history_entry = WorkspaceHistory(
                workspace_id=workspace.id,
                action="Cohort Deleted",
                phase="Data Analysis",
                creator_id=user_id,
                date=datetime.now(timezone.utc),
                description=f"Cohort {cohort.id} deleted."
            )
            db.add(history_entry)
            db.commit()
        else:
            raise ValueError(f"Workspace {cohort.workspace_id} not found for cohort {cohort_id}")
        return None
    
    def get_cohort_by_id(
        self, db: Session, cohort_id: int
    ) -> Optional[Cohort]:
        """
        Get a cohort by its ID.
        """
        return db.query(Cohort).filter(Cohort.id == cohort_id).first()