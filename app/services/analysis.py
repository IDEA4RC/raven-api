"""
Service for handling analysis operations
"""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.analysis import Analysis
from app.models.workspace import Workspace
from app.models.workspace_history import WorkspaceHistory
from app.schemas.analysis import AnalysisCreate, AnalysisUpdate
from app.services.base import BaseService
from app.models.cohort import Cohort
from app.services.cohort import CohortService

cohort_service = CohortService(Cohort)

class AnalysisService(BaseService[Analysis, AnalysisCreate, AnalysisUpdate]):
    """
    Service for handling analysis operations
    """

    def create_with_history(
        self,
        db: Session,
        *,
        obj_in: AnalysisCreate,
        user_id: int
    ) -> Analysis:
        """
        Create a new analysis and log the event in the workspace history
        """
        # Verificar que el workspace existe
        workspace = db.query(Workspace).filter(Workspace.id == obj_in.workspace_id).first()
        if not workspace:
            raise ValueError(f"Workspace with id {obj_in.workspace_id} not found")
            
        # Crear el análisis
        obj_in_data = obj_in.model_dump()
        if not obj_in_data.get("creation_date"):
            obj_in_data["creation_date"] = datetime.now(timezone.utc)
        if not obj_in_data.get("update_date"):
            obj_in_data["update_date"] = datetime.now(timezone.utc)
        obj_in_data["user_id"] = user_id
        db_obj = Analysis(**obj_in_data)
        db.add(db_obj)
        db.flush()
        
        # Crear historial
        workspace_history = WorkspaceHistory(
            date=datetime.now(timezone.utc),
            action="Analysis created",
            phase="Data Analysis",
            description=f"A new analysis has been created: '{db_obj.analysis_name}'",
            creator_id=user_id,
            workspace_id=obj_in.workspace_id
        )
        db.add(workspace_history)
        db.commit()
        db.refresh(db_obj)
        
        return db_obj

    def update_with_history(
        self,
        db: Session,
        *,
        analysis_id: int,
        obj_in: AnalysisUpdate,
        user_id: int,
    ) -> Analysis:
        """
        Update an analysis and log the change in workspace history
        """
        # Get the analysis
        analysis = self.get(db, analysis_id)
        if not analysis:
            raise ValueError(f"Analysis with id {analysis_id} not found")

        # Store old values for history
        old_name = analysis.analysis_name
        old_description = analysis.analysis_description
        old_expiring_date = analysis.expiring_date
        
        # Update the analysis
        obj_in_data = obj_in.model_dump(exclude_unset=True)
        obj_in_data["update_date"] = datetime.now(timezone.utc)
        
        updated_analysis = self.update(db, db_obj=analysis, obj_in=obj_in_data)

        # Track what changed for history
        changes = []
        if obj_in.analysis_name is not None and updated_analysis.analysis_name != old_name:
            changes.append(f"name from '{old_name}' to '{updated_analysis.analysis_name}'")
        if obj_in.analysis_description is not None and updated_analysis.analysis_description != old_description:
            changes.append("description")
        if obj_in.expiring_date is not None and updated_analysis.expiring_date != old_expiring_date:
            changes.append("expiring date")

        # Create workspace history if there were changes
        if changes:
            action = "Analysis updated"
            description = f"Analysis '{updated_analysis.analysis_name}' has been updated. Changes: {', '.join(changes)}"

            workspace_history = WorkspaceHistory(
                date=datetime.now(timezone.utc),
                phase="Data Analysis",
                action=action,
                description=description,
                creator_id=user_id,
                workspace_id=updated_analysis.workspace_id
            )
            db.add(workspace_history)
        
        db.commit()
        db.refresh(updated_analysis)
        return updated_analysis

    def delete_with_history(
        self,
        db: Session,
        *,
        analysis_id: int,
        user_id: int,
    ) -> Analysis:
        """
        Delete an analysis and log the change in workspace history
        """
        # Get the analysis
        analysis = self.get(db, analysis_id)
        if not analysis:
            raise ValueError(f"Analysis with id {analysis_id} not found")

        #  Buscar todos los cohorts relacionados con este analysis
        cohorts = db.query(Cohort).filter(Cohort.analysis_id == analysis_id).all()

        # 2️ Borrar los cohorts
        for cohort in cohorts:
            db.delete(cohort)


        # Store values for history before deletion
        workspace_id = analysis.workspace_id
        analysis_name = analysis.analysis_name
        
        # Delete the analysis
        deleted_analysis = self.remove(db, id=analysis_id)

        # Create workspace history entry
        workspace_history = WorkspaceHistory(
            date=datetime.now(timezone.utc),
            action="Analysis deleted",
            phase="Data Analysis",
            description=f"Analysis '{analysis_name}' has been deleted",
            creator_id=user_id,
            workspace_id=workspace_id
        )
        db.add(workspace_history)
        db.commit()
        
        return deleted_analysis

    def delete_with_history_and_cohorts(
        self,
        db: Session,
        *,
        analysis_id: int,
        user_id: int,
    ) -> Analysis:
        """
        Delete an analysis and log the change in workspace history
        """
        # Get the analysis
        analysis = self.get(db, analysis_id)
        if not analysis:
            raise ValueError(f"Analysis with id {analysis_id} not found")

        #  Buscar todos los cohorts relacionados con este analysis
        cohorts = db.query(Cohort).filter(Cohort.analysis_id == analysis_id).all()

        # 2️ Borrar los cohorts
        for cohort in cohorts:
            cohort_service.delete_cohort(db, cohort.id, user_id)
            
        # Store values for history before deletion
        workspace_id = analysis.workspace_id
        analysis_name = analysis.analysis_name
        
        # Delete the analysis
        deleted_analysis = self.remove(db, id=analysis_id)

        # Create workspace history entry
        workspace_history = WorkspaceHistory(
            date=datetime.now(timezone.utc),
            action="Analysis deleted",
            phase="Data Analysis",
            description=f"Analysis '{analysis_name}' has been deleted",
            creator_id=user_id,
            workspace_id=workspace_id
        )
        db.add(workspace_history)
        db.commit()
        
        return deleted_analysis

    def get_analyses_by_workspace(
        self,
        db: Session,
        *,
        workspace_id: int
    ) -> List[Analysis]:
        """
        Get all analyses for a specific workspace
        """
        return db.query(Analysis).filter(Analysis.workspace_id == workspace_id).all()

    def get_analyses_by_user(
        self,
        db: Session,
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Analysis]:
        """
        Get all analyses for a specific user with pagination
        """
        return db.query(Analysis)\
            .filter(Analysis.user_id == user_id)\
            .offset(skip)\
            .limit(limit)\
            .all()

    def get_expired_analyses(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Analysis]:
        """
        Get all expired analyses
        """
        current_time = datetime.now(timezone.utc)
        return db.query(Analysis)\
            .filter(Analysis.expiring_date < current_time)\
            .offset(skip)\
            .limit(limit)\
            .all()

    def get_analyses_expiring_soon(
        self,
        db: Session,
        *,
        days: int = 7,
        skip: int = 0,
        limit: int = 100
    ) -> List[Analysis]:
        """
        Get all analyses expiring within the specified number of days
        """
        from datetime import timedelta
        current_time = datetime.now(timezone.utc)
        expiring_threshold = current_time + timedelta(days=days)
        
        return db.query(Analysis)\
            .filter(Analysis.expiring_date <= expiring_threshold)\
            .filter(Analysis.expiring_date > current_time)\
            .offset(skip)\
            .limit(limit)\
            .all()


# Create a singleton instance
analysis_service = AnalysisService(Analysis)
