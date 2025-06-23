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

@router.get("/", response_model=List[schemas.WorkspaceHistory])
def get_all_workspace_histories(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Obtains all workspace histories.
    """
    try:
        histories = db.query(WorkspaceHistory)\
            .order_by(WorkspaceHistory.date.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()
        return histories
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving workspace histories: {str(e)}"
        )

