"""
Service for handling permit operations
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.permit import Permit
from app.models.workspace import Workspace
from app.models.workspace_history import WorkspaceHistory
from app.schemas.permit import PermitCreate, PermitUpdate
from app.services.base import BaseService
from app.utils.constants import PermitStatus, DataAccessStatus


class PermitService(BaseService[Permit, PermitCreate, PermitUpdate]):
    """
    Service for handling permit operations
    """

    def create_with_history(
        self,
        db: Session,
        *,
        obj_in: PermitCreate,
        user_id: int
    ) -> Permit:
        """
        Create a new permit and log the event in the workspace history
        """
        # Verificar que el workspace existe
        workspace = db.query(Workspace).filter(Workspace.id == obj_in.workspace_id).first()
        if not workspace:
            raise ValueError(f"Workspace with id {obj_in.workspace_id} not found")
            
        # Crear el permiso
        obj_in_data = obj_in.dict()
        if not obj_in_data.get("update_date"):
            obj_in_data["update_date"] = datetime.utcnow()
        db_obj = Permit(**obj_in_data)
        db.add(db_obj)
        db.flush()
        
        # Actualizar el workspace
        workspace.data_access = db_obj.status
        workspace.last_modification_date = datetime.utcnow()
        db.add(workspace)
        
        # Crear historial
        action = f"Permit created with status {db_obj.status}"
        if db_obj.status == 2:
            action = "Submitted data access application"
            description = "The data permit application has been submitted"
        else:
            description = f"A new permit with status {db_obj.status} has been created"
            
        workspace_history = WorkspaceHistory(
            date=datetime.utcnow(),
            action=action,
            description=description,
            user_id=user_id,
            workspace_id=obj_in.workspace_id
        )
        db.add(workspace_history)
        db.commit()
        db.refresh(db_obj)
        
        return db_obj

    def update_permit_status(
        self,
        db: Session,
        *,
        permit_id: int,
        status: int,
        user_id: int
    ) -> Permit:
        """
        Update the status of a permit and log the change in workspace and workspace history
        """
        # Get the permit
        permit = self.get(db, permit_id)
        if not permit:
            raise ValueError(f"Permit with id {permit_id} not found")

        # Update the permit status
        permit_update = PermitUpdate(
            status=status,
            update_date=datetime.utcnow()
        )
        updated_permit = self.update(db, db_obj=permit, obj_in=permit_update)

        # Update the workspace
        workspace = db.query(Workspace).filter(Workspace.id == permit.workspace_id).first()
        if workspace:
            workspace.data_access = status
            workspace.last_modification_date = datetime.utcnow()
            db.add(workspace)

        # Crear historial de workspace
        action = f"Permit status updated to {status}"
        if status == PermitStatus.SUBMITTED:
            action = "Submitted data access application"
            description = "The data permit application has been submitted"
        elif status == PermitStatus.APPROVED:
            action = "Data access application approved"
            description = "The data permit application has been approved"
        elif status == PermitStatus.REJECTED:
            action = "Data access application rejected"
            description = "The data permit application has been rejected"
        else:
            description = f"The permit status has been changed to {status}"

        workspace_history = WorkspaceHistory(
            date=datetime.utcnow(),
            action=action,
            description=description,
            user_id=user_id,
            workspace_id=permit.workspace_id
        )
        db.add(workspace_history)
        db.commit()
        db.refresh(workspace_history)

        return updated_permit


permit_service = PermitService(Permit)