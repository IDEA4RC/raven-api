"""
Endpoints for analysis operations
"""

from typing import List, Any

from app.utils.constants import TOKEN_V6
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.algorithms import algorithm_service
from app.schemas.algorithms import Algorithm as AlgorithmSchema
from app.schemas.algorithms import AlgorithmUpdate
from app.schemas.CohortListRequest import CohortListRequest
from app import schemas

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=List[schemas.algorithms.Algorithm])
def get_all_algorithms(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Obtains all analyses with pagination.
    """
    try:
        algorithms = algorithm_service.get_all_algorithm(db=db)
        return algorithms

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

    # Return a safely-serialized list to avoid strict Pydantic validation issues


@router.get(
    "/get_by_cohort/{cohort_id}", response_model=List[schemas.algorithms.Algorithm]
)
def get_by_cohort(
    *,
    db: Session = Depends(get_db),
    cohort_id: int,
    current_user: User = Depends(get_current_user),
) -> any:
    """
    Obtains all analyses with pagination.
    """
    try:

        algorithms = algorithm_service.get_algorithms_by_cohort(
            db=db, cohort_id=cohort_id
        )
        return algorithms

    except Exception as e:

        raise HTTPException(status_code=500, detail="Internal server error")

    # Return a safely-serialized list to avoid strict Pydantic validation issues


@router.post("/by_cohorts_list", response_model=List[schemas.algorithms.Algorithm])
def get_algorithms_by_cohorts(
    request: CohortListRequest,
    db: Session = Depends(get_db),
):
    try:

        algorithms = algorithm_service.get_algorithms_by_exact_cohort_list(
            db, request.cohort_ids
        )

        return algorithms
    except Exception as e:

        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/is_summary", response_model=List[schemas.algorithms.Algorithm])
def is_summary_by_cohorts(
    request: CohortListRequest,
    db: Session = Depends(get_db),
):
    try:

        algorithms = algorithm_service.is_summary_cohort_list(db, request.cohort_ids)

        return algorithms
    except Exception as e:

        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/update_algorithm", response_model=schemas.algorithms.Algorithm)
def update_algorithm(
    request: AlgorithmUpdate,
    db: Session = Depends(get_db),
):
    try:
        algorithms = algorithm_service.update_algorithm(db, obj_in=request)
        return algorithms
    except Exception as e:
        logger.exception("Error updating task status")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/algorithms_statistics/{task_id}")
def get_algorithm_statistics(
    task_id: int,
    db: Session = Depends(get_db),
) -> Any:
    try:
        algorithms = algorithm_service.get_algorithm_statistics(
            access_token=TOKEN_V6, task_id=task_id
        )
        return algorithms
    except Exception as e:
        logger.exception("Error updating task status")
        raise HTTPException(status_code=500, detail="Internal server error")
