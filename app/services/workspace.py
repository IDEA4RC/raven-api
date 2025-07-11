"""
Servicio para operaciones con workspaces
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.workspace import Workspace
from app.models.workspace_history import WorkspaceHistory
from app.models.permit import Permit
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate
from app.services.base import BaseService
from app.utils.constants import PermitStatus, DataAccessStatus


class WorkspaceService(BaseService[Workspace, WorkspaceCreate, WorkspaceUpdate]):
    """
    Service for handling workspace operations
    """

    def create_with_history(
        self,
        db: Session,
        *,
        obj_in: WorkspaceCreate,
        user_id: int
    ) -> Workspace:
        """
        Create a new workspace and log the event in the workspace history
        """
        # Crear workspace
        obj_in_data = obj_in.model_dump()
        db_obj = Workspace(**obj_in_data)
        db_obj.creator_id = user_id
        db.add(db_obj)
        db.flush()  # Para obtener el ID sin hacer commit

        # Crear historial
        workspace_history = WorkspaceHistory(
            date=datetime.now(timezone.utc),
            action="Created workspace",
            description="Workspace created successfully",
            workspace_id=db_obj.id,
            creator_id=user_id
        )
        db.add(workspace_history)
        
        # Crear registro de permiso inicial (estado pendiente)
        permit = Permit(
            status=PermitStatus.PENDING,  # 1 = Pending
            update_date=datetime.now(timezone.utc),
            workspace_id=db_obj.id,
            team_ids=db_obj.team_ids or [],
        )
        db.add(permit)
        
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_data_access(
        self,
        db: Session,
        *,
        workspace_id: int,
        data_access: int,
        user_id: int
    ) -> Workspace:
        """
        Update the data access status of a workspace and log the change
        """
        # Get the workspace
        workspace = self.get(db, workspace_id)
        if not workspace:
            raise ValueError(f"Workspace with id {workspace_id} not found")

        # Actualizar el workspace
        workspace_update = WorkspaceUpdate(
            data_access=data_access,
            last_modification_date=datetime.now(timezone.utc)
        )
        updated_workspace = self.update(db, db_obj=workspace, obj_in=workspace_update)

        # Crear historial
        action = f"Updated data access to {data_access}"
        description = ""
        if data_access == DataAccessStatus.SUBMITTED:
            action = "Submitted data access"
            description = "The data access request has been submitted"
        elif data_access == DataAccessStatus.APPROVED:
            action = "Data access approved"
            description = "The data access request has been approved"
        elif data_access == DataAccessStatus.REJECTED:
            action = "Data access rejected"
            description = "The data access request has been rejected"
        else:
            description = f"Data access status has been changed to {data_access}"

        workspace_history = WorkspaceHistory(
            date=datetime.now(timezone.utc),
            action=action,
            description=description,
            creator_id=user_id,
            workspace_id=workspace_id
        )
        db.add(workspace_history)
        db.commit()
        db.refresh(workspace_history)

        return updated_workspace


workspace_service = WorkspaceService(Workspace)