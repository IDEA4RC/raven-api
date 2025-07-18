"""
Endpoints for permit operations
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.permit import Permit
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
    Creates a new permit for a workspace.
    """
    permit = permit_service.create_with_history(db=db, obj_in=permit_in, user_id=current_user.id)
    return permit


@router.get("/", response_model=List[schemas.Permit])
def get_permits(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Obtains all permits.
    """
    permits = permit_service.get_multi(db=db, skip=skip, limit=limit)
    return permits


@router.get("/{permit_id}", response_model=schemas.Permit)
def get_permit(
    *,
    db: Session = Depends(get_db),
    permit_id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Obtains a permit by ID.
    """
    permit = permit_service.get(db=db, id=permit_id)
    if not permit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permit with ID {permit_id} not found"
        )
    return permit


@router.patch("/{permit_id}", response_model=schemas.Permit)
def update_permit(
    *,
    db: Session = Depends(get_db),
    permit_id: int,
    permit_in: schemas.PermitUpdate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Updates a permit (PATCH operation).
    """
    try:
        permit = permit_service.update_with_history(
            db=db, permit_id=permit_id, obj_in=permit_in, user_id=current_user.id
        )
        return permit
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{permit_id}", status_code=status.HTTP_200_OK)
def delete_permit(
    *,
    db: Session = Depends(get_db),
    permit_id: int,
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Deletes a permit.
    """
    try:
        deleted_permit = permit_service.delete_with_history(
            db=db, permit_id=permit_id, user_id=current_user.id
        )
        return deleted_permit
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/workspace/{workspace_id}", response_model=List[schemas.Permit])
def get_permits_by_workspace(
    *,
    db: Session = Depends(get_db),
    workspace_id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Obtains all permits for a workspace.
    """
    permits = db.query(Permit)\
        .filter(Permit.workspace_id == workspace_id)\
        .all()
    return permits


@router.get("/team/{team_id}", response_model=List[schemas.Permit])
def get_permits_by_team(
    *,
    db: Session = Depends(get_db),
    team_id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Obtains all permits for a team.
    """
    permits = db.query(Permit)\
        .filter(Permit.team_id == team_id)\
        .all()
    return permits


@router.patch("/{permit_id}/status", response_model=schemas.Permit)
def update_permit_status(
    *,
    db: Session = Depends(get_db),
    permit_id: int,
    permit_update: schemas.PermitUpdate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Updates the status of a permit.
    """
    if permit_update.status is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status field is required"
        )
    
    try:
        permit = permit_service.update_permit_status(
            db=db, permit_id=permit_id, status=permit_update.status, user_id=current_user.id, phase="Data Permit"
        )
        return permit
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
