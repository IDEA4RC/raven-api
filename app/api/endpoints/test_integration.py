"""
Endpoints for testing integration between Permit, Workspace and WorkspaceHistory
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.workspace import workspace_service
from app.services.permit import permit_service
from app.utils.constants import PermitStatus, DataAccessStatus

router = APIRouter()


@router.post("/submit-permit-request", response_model=Dict[str, Any])
def submit_permit_request(
    *,
    db: Session = Depends(get_db),
    workspace_id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Sends a permit request for a workspace.
    Updates the permit status, the workspace, and creates a record in the history.
    """
    try:
        # 1. Get the current permit for the workspace
        permits = db.query(permit_service.model)\
            .filter(permit_service.model.workspace_id == workspace_id)\
            .all()
        
        if not permits:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No permit found for workspace {workspace_id}"
            )
        
        # Usar el permiso más reciente si hay varios
        permit = permits[0]
        
        # 2. Actualizar el permiso a estado "Submitted"
        updated_permit = permit_service.update_permit_status(
            db=db, permit_id=permit.id, status=PermitStatus.SUBMITTED, user_id=current_user.id
        )
        
        # 3. Actualizar el workspace
        updated_workspace = workspace_service.update_data_access(
            db=db, workspace_id=workspace_id, data_access=DataAccessStatus.SUBMITTED, user_id=current_user.id
        )
        
        # 4. Obtener el historial actualizado
        from app.models.workspace_history import WorkspaceHistory
        history = db.query(WorkspaceHistory)\
            .filter(WorkspaceHistory.workspace_id == workspace_id)\
            .order_by(WorkspaceHistory.date.desc())\
            .all()
        
        return {
            "success": True,
            "message": "Permit request submitted successfully",
            "permit": updated_permit,
            "workspace": updated_workspace,
            "history_entries": len(history)
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting permit request: {str(e)}"
        )
