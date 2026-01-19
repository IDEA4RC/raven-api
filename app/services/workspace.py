"""
Servicio para operaciones con workspaces
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.workspace import Workspace
from app.models.workspace_history import WorkspaceHistory
from app.models.permit import Permit
from app.models.metadata_search import MetadataSearch
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate, WorkspaceCreateV2
from app.services.base import BaseService
from app.utils.constants import PermitStatus, DataAccessStatus, MetadataStatus


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
            phase="Data permit",
            description="Workspace created successfully",
            workspace_id=db_obj.id,
            creator_id=user_id
        )
        db.add(workspace_history)
        
        # Crear registro de permiso inicial (estado pendiente)
        permit = Permit(
            status=PermitStatus.PENDING,  # 0 = Pending
            update_date=datetime.now(timezone.utc),
            workspace_id=db_obj.id,
            team_ids=db_obj.team_ids or [],
        )
        db.add(permit)
        
        permit_workspace_history = WorkspaceHistory(
            date=datetime.now(timezone.utc),
            action="Initial permit created",
            phase="Data Permit",
            description="Initial permit created with status Pending",
            creator_id=user_id,
            workspace_id=db_obj.id
        )
        db.add(permit_workspace_history)

        
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def create_with_history_v2(
        self,
        db: Session,
        *,
        obj_in: WorkspaceCreateV2,
        user_id: int, 
        access_token: str
    ) -> Workspace:
        """
        Create a new workspace and log the event in the workspace history.
        """

        def create_workspace(db, obj_in_data, user_id):
            workspace_columns = set(Workspace.__table__.columns.keys())
            workspace_data = {k: v for k, v in obj_in_data.items() if k in workspace_columns}
            db_obj = Workspace(**workspace_data)
            db_obj.creator_id = user_id
            db.add(db_obj)
            db.flush()  # Para obtener el ID sin hacer commit
            return db_obj

        def create_workspace_history(db, workspace_id, user_id, action, phase, description):
            history = WorkspaceHistory(
                date=datetime.now(timezone.utc),
                action=action,
                phase=phase,
                description=description,
                workspace_id=workspace_id,
                creator_id=user_id
            )
            db.add(history)

        def create_initial_permit(db, workspace_id, team_ids, user_id):
            permit = Permit(
                status=PermitStatus.PENDING,
                update_date=datetime.now(timezone.utc),
                workspace_id=workspace_id,
                team_ids=team_ids or [],
            )
            db.add(permit)

            create_workspace_history(
                db,
                workspace_id=workspace_id,
                user_id=user_id,
                action="Iniciated data access application",
                phase="Data permit",
                description="The data permit application has been iniciated to request data access"
            )

        def create_metadata(db, workspace_id, obj_in):
            metadata = MetadataSearch(
                workspace_id=workspace_id,
                type_cancer=obj_in.type_cancer or "",
                status=MetadataStatus.COMPLETED,
                update_date=datetime.now(timezone.utc),
                created_date=datetime.now(timezone.utc),
                id_variables=obj_in.id_variables or [],
                selected_id_coes=obj_in.selected_id_coes or []
            )
            db.add(metadata)

        # --- Flujo principal ---
        obj_in_data = obj_in.model_dump()
        db_obj = create_workspace(db, obj_in_data, user_id)
        create_metadata(db, workspace_id=db_obj.id, obj_in=obj_in)

        create_workspace_history(
            db,
            workspace_id=db_obj.id,
            user_id=user_id,
            action="Created workspace",
            phase="Metadata Search",
            description="Metadata Search has been finished and the workspace has been created"
        )

        create_initial_permit(db, workspace_id=db_obj.id, team_ids=db_obj.team_ids, user_id=user_id)
       
        db.commit()
        db.refresh(db_obj)

        db_obj["access_token"] = access_token  # Store access token if needed

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
        elif data_access == DataAccessStatus.GRANTED:
            action = "Data access approved"
            description = "The data access request has been approved"
        elif data_access == DataAccessStatus.REJECTED:
            action = "Data access rejected"
            description = "The data access request has been rejected"
        elif data_access == DataAccessStatus.EXPIRED:
            action = "Data access expired"
            description = "The data access request has expired"
        elif data_access == DataAccessStatus.INICIATED:
            action = "Data access initiated"
            description = "The data access request has been initiated"
        else:
            description = f"Data access status has been changed to {data_access}"

        workspace_history = WorkspaceHistory(
            date=datetime.now(timezone.utc),
            action=action,
            phase="Data Access",
            description=description,
            creator_id=user_id,
            workspace_id=workspace_id
        )
        db.add(workspace_history)
        db.commit()
        db.refresh(workspace_history)

        return updated_workspace


workspace_service = WorkspaceService(Workspace)