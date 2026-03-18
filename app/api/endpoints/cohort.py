"""
Endpoints for cohort operations
"""

from typing import Any, List, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import schemas
from app.api.deps import get_current_user, get_db, get_current_user_with_token
from app.models.user import User
from app.api import CurrentUserContext

from app.models.cohort import Cohort
from app.services.cohort import CohortService

router = APIRouter()
from app.utils.constants import TOKEN_V6

# Initialize the cohort service
cohort_service = CohortService(Cohort)

import logging

logger = logging.getLogger(__name__)


@router.post("/", response_model=schemas.Cohort, status_code=status.HTTP_201_CREATED)
def create_cohort(
    *,
    db: Session = Depends(get_db),
    cohort_in: schemas.CohortCreate,
    current_user: CurrentUserContext = Depends(get_current_user_with_token),
) -> Any:
    """
    Creates a new cohort for a workspace.
    """
    try:

        logger.info(
            "[COHORT] Cohort post service with ID cohort_name=%s, analysis_id=%s",
            cohort_in.cohort_name,
            cohort_in.analysis_id,
        )
        user = current_user.user
        # access_token = current_user.access_token
        cohort = cohort_service.create_with_history_v2(
            db=db, obj_in=cohort_in, user_id=user.id
        )
        return cohort
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))  # fallo externo

    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/")
def get_cohorts(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Obtains all cohorts with pagination.
    """
    cohorts = cohort_service.get_all_cohorts(db=db, skip=skip, limit=limit)

    def serialize(c: Any) -> Dict[str, Any]:
        fields = [
            "id",
            "cohort_name",
            "cohort_description",
            "cohort_query",
            "creation_date",
            "update_date",
            "status",
            "user_id",
            "analysis_id",
            "workspace_id",
            "query_execution_id",
        ]
        return {
            k: getattr(c, k)
            for k in fields
            if hasattr(c, k) and getattr(c, k) is not None
        }

    return [serialize(c) for c in cohorts]


@router.get("/{cohort_id}", response_model=schemas.cohort.Cohort)
def get_cohort(
    *,
    db: Session = Depends(get_db),
    cohort_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Obtains a cohort by ID.
    """
    cohort = cohort_service.get_cohort_by_id(db=db, cohort_id=cohort_id)
    if not cohort:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cohort with ID {cohort_id} not found",
        )
    return cohort


@router.patch("/{cohort_id}", response_model=schemas.cohort.Cohort)
def update_cohort(
    *,
    db: Session = Depends(get_db),
    cohort_id: int,
    cohort_in: schemas.cohort.CohortUpdate,
    current_user: User = Depends(get_current_user),
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{cohort_id}/status", response_model=schemas.cohort.Cohort)
def update_cohort_status(
    *,
    db: Session = Depends(get_db),
    cohort_id: int,
    status_update: schemas.cohort.CohortStatusUpdate,
    current_user: User = Depends(get_current_user),
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{cohort_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cohort(
    *,
    db: Session = Depends(get_db),
    cohort_id: int,
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Deletes a cohort.
    """
    try:
        cohort_service.delete_cohort(
            db=db, cohort_id=cohort_id, user_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/workspace/{workspace_id}", response_model=List[schemas.cohort.Cohort])
def get_cohorts_by_workspace(
    *,
    db: Session = Depends(get_db),
    workspace_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Obtains all cohorts for a workspace.
    """
    cohorts = cohort_service.get_cohorts_by_workspace(db=db, workspace_id=workspace_id)
    return cohorts


@router.get("/analysis/{analysis_id_in}", response_model=List[schemas.Cohort])
def get_cohorts_by_analysis(
    *,
    db: Session = Depends(get_db),
    analysis_id_in: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Obtains all cohorts for a workspace.
    """
    cohorts = cohort_service.get_cohorts_by_analysis(db=db, analysis_id=analysis_id_in)
    return cohorts


@router.post(
    "/create_vantage",
    response_model=schemas.Cohort,
    status_code=status.HTTP_201_CREATED,
)
def create_cohort(
    *,
    db: Session = Depends(get_db),
    cohort_in: schemas.CohortCreate,
    current_user: CurrentUserContext = Depends(get_current_user_with_token),
) -> Any:
    """
    Creates a new cohort for a workspace.
    """

    try:
        user = current_user.user
        # access_token = current_user.access_token

        cohort = cohort_service.create_with_history_v2(
            db=db, obj_in=cohort_in, user_id=user.id  # , access_token=TOKEN_V6
        )
        return cohort
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
