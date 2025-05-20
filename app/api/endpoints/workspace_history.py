"""
Endpoints for operations with the workspace history
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.workspace_history import WorkspaceHistory

router = APIRouter()


@router.get("/{workspace_id}", response_model=List[schemas.WorkspaceHistory])
def get_workspace_history(
    *,
    db: Session = Depends(get_db),
    workspace_id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Obtains the complete history of a workspace.
    """
    history = db.query(WorkspaceHistory)\
        .filter(WorkspaceHistory.workspace_id == workspace_id)\
        .order_by(WorkspaceHistory.date.desc())\
        .all()
    return history
