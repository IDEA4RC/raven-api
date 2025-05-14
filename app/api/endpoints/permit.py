"""
Endpoints para operaciones con permisos
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.permit import permit_service

router = APIRouter()


@router.post("/", response_model=schemas.Permit, status_code=status.HTTP_201_CREATED)
def create_permit(
    *,
    db: Session = Depends(get_db),
    permit_in: schemas.PermitCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Crea un nuevo permiso para un workspace.
    """
    permit = permit_service.create(db=db, obj_in=permit_in)
    return permit


@router.get("/{permit_id}", response_model=schemas.Permit)
def get_permit(
    *,
    db: Session = Depends(get_db),
    permit_id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Obtiene un permiso por ID.
    """
    permit = permit_service.get(db=db, id=permit_id)
    if not permit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permit with ID {permit_id} not found"
        )
    return permit


@router.get("/workspace/{workspace_id}", response_model=List[schemas.Permit])
def get_permits_by_workspace(
    *,
    db: Session = Depends(get_db),
    workspace_id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Obtiene todos los permisos de un workspace.
    """
    permits = db.query(permit_service.model)\
        .filter(permit_service.model.workspace_id == workspace_id)\
        .all()
    return permits


@router.patch("/{permit_id}/status", response_model=schemas.Permit)
def update_permit_status(
    *,
    db: Session = Depends(get_db),
    permit_id: int,
    status: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Actualiza el estado de un permiso.
    """
    try:
        permit = permit_service.update_permit_status(
            db=db, permit_id=permit_id, status=status, user_id=current_user.id
        )
        return permit
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
