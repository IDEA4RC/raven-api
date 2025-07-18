"""
Service for handling permit operations
"""

from datetime import datetime, timezone
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
        obj_in_data = obj_in.model_dump()
        if not obj_in_data.get("update_date"):
            obj_in_data["update_date"] = datetime.now(timezone.utc)
        db_obj = Permit(**obj_in_data)
        db.add(db_obj)
        db.flush()
        
        # Actualizar el workspace
        workspace.data_access = db_obj.status
        workspace.last_modification_date = datetime.now(timezone.utc)
        db.add(workspace)
        
        # Crear historial
        action = f"Permit created with status {db_obj.status}"
        if db_obj.status == PermitStatus.SUBMITTED:
            action = "Submitted data access application"
            description = "The data permit application has been submitted"
        else:
            description = f"A new permit with status {db_obj.status} has been created"
            
        workspace_history = WorkspaceHistory(
            date=datetime.now(timezone.utc),
            action=action,
            phase="Data Permit",
            description=description,
            creator_id=user_id,
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
        user_id: int,
        phase: str
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
            update_date=datetime.now(timezone.utc)
        )
        updated_permit = self.update(db, db_obj=permit, obj_in=permit_update)

        # Update the workspace
        workspace = db.query(Workspace).filter(Workspace.id == permit.workspace_id).first()
        if workspace:
            workspace.data_access = status
            workspace.last_modification_date = datetime.now(timezone.utc)
            db.add(workspace)

        # Crear historial de workspace
        action = f"Permit status updated to {status}"
        if status == PermitStatus.SUBMITTED:
            action = "Submitted data access application"
            description = "The data permit application has been submitted"
        elif status == PermitStatus.INICIATED:
            action = "Data access application initiated"
            description = "The data permit application has been initiated"
        elif status == PermitStatus.GRANTED:
            action = "Data access application approved"
            description = "The data permit application has been approved"
        elif status == PermitStatus.REJECTED:
            action = "Data access application rejected"
            description = "The data permit application has been rejected"
        elif status == PermitStatus.EXPIRED:
            action = "Data access permit expired"
            description = "The data permit has expired"
        else:
            description = f"The permit status has been changed to {status}"

        workspace_history = WorkspaceHistory(
            date=datetime.now(timezone.utc),
            action=action,
            phase="Data Permit",
            description=description,
            creator_id=user_id,
            workspace_id=permit.workspace_id
        )
        db.add(workspace_history)
        db.commit()
        db.refresh(workspace_history)

        return updated_permit

    def update_with_history(
        self,
        db: Session,
        *,
        permit_id: int,
        obj_in: PermitUpdate,
        user_id: int,
    ) -> Permit:
        """
        Update a permit and log the change in workspace history
        """
        # Get the permit
        permit = self.get(db, permit_id)
        if not permit:
            raise ValueError(f"Permit with id {permit_id} not found")

        # Store old values for history
        old_status = permit.status
        old_permit_name = permit.permit_name
        old_expiration_date = permit.expiration_date
        old_team_ids = permit.team_ids
        old_coes_granted = permit.coes_granted
        
        # Handle user_team_ids -> team_ids mapping
        if obj_in.user_team_ids is not None:
            obj_in.team_ids = obj_in.user_team_ids
            # Remove user_team_ids from the update object to avoid passing it to the base service
            obj_in_dict = obj_in.dict(exclude_unset=True)
            obj_in_dict.pop('user_team_ids', None)
            obj_in = PermitUpdate(**obj_in_dict)
        
        # Validate coes_granted - only allow if status is GRANTED
        if obj_in.coes_granted is not None:
            if obj_in.status is not None and obj_in.status != PermitStatus.GRANTED:
                raise ValueError("coes_granted can only be set when status is GRANTED")
            elif obj_in.status is None and permit.status != PermitStatus.GRANTED:
                raise ValueError("coes_granted can only be set when status is GRANTED")
        
        # Update the permit
        if obj_in.update_date is None:
            obj_in.update_date = datetime.now(timezone.utc)
        updated_permit = self.update(db, db_obj=permit, obj_in=obj_in)

        # Track what changed for history
        changes = []
        if obj_in.status is not None and updated_permit.status != old_status:
            changes.append(f"status from {old_status} to {updated_permit.status}")
        if obj_in.permit_name is not None and updated_permit.permit_name != old_permit_name:
            changes.append(f"permit name")
        if obj_in.expiration_date is not None and updated_permit.expiration_date != old_expiration_date:
            changes.append(f"expiration date")
        if obj_in.team_ids is not None and updated_permit.team_ids != old_team_ids:
            changes.append(f"team assignments")
        if obj_in.coes_granted is not None and updated_permit.coes_granted != old_coes_granted:
            changes.append(f"COEs granted")

        # Update the workspace if status changed
        if obj_in.status is not None and updated_permit.status != old_status:
            workspace = db.query(Workspace).filter(Workspace.id == updated_permit.workspace_id).first()
            if workspace:
                workspace.data_access = updated_permit.status
                workspace.last_modification_date = datetime.now(timezone.utc)
                db.add(workspace)

        # Create workspace history if there were changes
        if changes:
            # Determine action based on changes
            if obj_in.status is not None and updated_permit.status != old_status:
                # Status change takes priority for action description
                action = f"Permit status updated from {old_status} to {updated_permit.status}"
                if updated_permit.status == PermitStatus.SUBMITTED:
                    action = "Submitted data access application"
                    description = "The data permit application has been submitted"
                elif updated_permit.status == PermitStatus.INICIATED:
                    action = "Data access application initiated"
                    description = "The data permit application has been initiated"
                elif updated_permit.status == PermitStatus.GRANTED:
                    action = "Data access application approved"
                    description = "The data permit application has been approved"
                elif updated_permit.status == PermitStatus.REJECTED:
                    action = "Data access application rejected"
                    description = "The data permit application has been rejected"
                elif updated_permit.status == PermitStatus.EXPIRED:
                    action = "Data access permit expired"
                    description = "The data permit has expired"
                else:
                    description = f"The permit status has been changed from {old_status} to {updated_permit.status}"
                
                # Add other changes to description if they exist
                if len(changes) > 1:
                    other_changes = [c for c in changes if not c.startswith("status")]
                    if other_changes:
                        description += f". Also updated: {', '.join(other_changes)}"
            else:
                # Only non-status changes
                action = f"Permit updated"
                description = f"Updated permit fields: {', '.join(changes)}"

            workspace_history = WorkspaceHistory(
                date=datetime.now(timezone.utc),
                phase="Data Permit",
                action=action,
                description=description,
                creator_id=user_id,
                workspace_id=updated_permit.workspace_id
            )
            db.add(workspace_history)
        
        db.commit()
        db.refresh(updated_permit)
        return updated_permit

    def delete_with_history(
        self,
        db: Session,
        *,
        permit_id: int,
        user_id: int,
    ) -> Permit:
        """
        Delete a permit and log the change in workspace history
        """
        # Get the permit
        permit = self.get(db, permit_id)
        if not permit:
            raise ValueError(f"Permit with id {permit_id} not found")

        # Store values for history before deletion
        workspace_id = permit.workspace_id
        permit_status = permit.status
        
        # Delete the permit
        deleted_permit = self.remove(db, id=permit_id)

        # Create workspace history entry
        workspace_history = WorkspaceHistory(
            date=datetime.now(timezone.utc),
            action=f"Permit deleted (was status {permit_status})",
            phase="Data Permit",
            description=f"A permit with status {permit_status} has been deleted",
            creator_id=user_id,
            workspace_id=workspace_id
        )
        db.add(workspace_history)
        db.commit()
        
        return deleted_permit


permit_service = PermitService(Permit)