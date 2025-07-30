"""
Endpoints for cohort operations
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.cohort import Cohort
from app.services.cohort import CohortService

router = APIRouter()

# Initialize the cohort service
cohort_service = CohortService(Cohort)


@router.post("/", response_model=schemas.cohort.Cohort, status_code=status.HTTP_201_CREATED)
def create_cohort(
    *,
    db: Session = Depends(get_db),
    cohort_in: schemas.cohort.CohortCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Creates a new cohort for a workspace.
    """
    try:
        cohort = cohort_service.create_with_history(
            db=db, obj_in=cohort_in, user_id=current_user.id
        )
        return cohort
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/", response_model=List[schemas.cohort.Cohort])
def get_cohorts(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Obtains all cohorts with pagination.
    """
    cohorts = cohort_service.get_all_cohorts(db=db, skip=skip, limit=limit)
    return cohorts


@router.get("/{cohort_id}", response_model=schemas.cohort.Cohort)
def get_cohort(
    *,
    db: Session = Depends(get_db),
    cohort_id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Obtains a cohort by ID.
    """
    cohort = cohort_service.get_cohort_by_id(db=db, cohort_id=cohort_id)
    if not cohort:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cohort with ID {cohort_id} not found"
        )
    return cohort


@router.patch("/{cohort_id}", response_model=schemas.cohort.Cohort)
def update_cohort(
    *,
    db: Session = Depends(get_db),
    cohort_id: int,
    cohort_in: schemas.cohort.CohortUpdate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Updates a cohort (PATCH operation).
    Can update any combination of: cohort_name, cohort_description, cohort_query, status.
    """
    try:
        cohort = cohort_service.update_cohort(
            db=db, obj_in=cohort_in, cohort_id=cohort_id, user_id=current_user.id
        )
        return cohort
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.patch("/{cohort_id}/status", response_model=schemas.cohort.Cohort)
def update_cohort_status(
    *,
    db: Session = Depends(get_db),
    cohort_id: int,
    status_update: schemas.cohort.CohortStatusUpdate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Updates the status of a cohort.
    """
    try:
        cohort = cohort_service.update_cohort_status(
            db=db, obj_in=status_update, cohort_id=cohort_id, user_id=current_user.id
        )
        return cohort
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{cohort_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cohort(
    *,
    db: Session = Depends(get_db),
    cohort_id: int,
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Deletes a cohort.
    """
    try:
        cohort_service.delete_cohort(
            db=db, cohort_id=cohort_id, user_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/workspace/{workspace_id}", response_model=List[schemas.cohort.Cohort])
def get_cohorts_by_workspace(
    *,
    db: Session = Depends(get_db),
    workspace_id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Obtains all cohorts for a workspace.
    """
    cohorts = cohort_service.get_cohorts_by_workspace(db=db, workspace_id=workspace_id)
    return cohorts
