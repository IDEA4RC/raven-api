"""
Endpoints para operaciones con workspaces
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.workspace import workspace_service

router = APIRouter()


@router.post("/", response_model=schemas.Workspace, status_code=status.HTTP_201_CREATED)
def create_workspace(
    *,
    db: Session = Depends(get_db),
    workspace_in: schemas.WorkspaceCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Crea un nuevo workspace.
    """
    workspace = workspace_service.create_with_history(
        db=db, obj_in=workspace_in, user_id=current_user.id
    )
    return workspace


@router.get("/{workspace_id}", response_model=schemas.Workspace)
def get_workspace(
    *,
    db: Session = Depends(get_db),
    workspace_id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Obtiene un workspace por ID.
    """
    workspace = workspace_service.get(db=db, id=workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace with ID {workspace_id} not found"
        )
    return workspace


@router.get("/", response_model=List[schemas.Workspace])
def get_workspaces(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Obtiene todos los workspaces.
    """
    workspaces = workspace_service.get_multi(db=db, skip=skip, limit=limit)
    return workspaces


@router.patch("/{workspace_id}/data-access", response_model=schemas.Workspace)
def update_data_access(
    *,
    db: Session = Depends(get_db),
    workspace_id: int,
    data_access: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Actualiza el estado de acceso a datos de un workspace.
    """
    workspace = workspace_service.update_data_access(
        db=db, workspace_id=workspace_id, data_access=data_access, user_id=current_user.id
    )
    return workspace
