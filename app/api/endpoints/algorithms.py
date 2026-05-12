"""
Endpoints for analysis operations
"""

from typing import List, Any

from alembic.util import status
from app.api.CurrentUserContext import CurrentUserContext
from app.services.vantage_6 import Vantage6Service
from app.utils.constants import TOKEN_V6
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from app.api.deps import get_current_user, get_current_user_with_token, get_db
from app.models.user import User
from app.services.algorithms import algorithm_service
from app.schemas.algorithms import Algorithm as AlgorithmSchema
from app.schemas.algorithms import AlgorithmUpdate
from app.schemas.CohortListRequest import CohortListRequest
from app import schemas

logger = logging.getLogger(__name__)
router = APIRouter()
service_vantage6 = Vantage6Service()


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
async def get_algorithms_by_cohorts(
    request: CohortListRequest,
    db: Session = Depends(get_db),
):
    logger.info(
        "[ALGORITHMS] POST to get_algorithms_by_cohorts with cohort_ids: %s",
        request.cohort_ids,
    )
    try:

        algorithms = await algorithm_service.get_algorithms_with_status_async(
            db, request.cohort_ids, TOKEN_V6
        )

        return algorithms
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Internal server error, error: %s" % str(e)
        )


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


@router.post("/areReadyDataframes", response_model=List[schemas.algorithms.Algorithm])
def are_ready_dataframes_by_cohorts(
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


@router.get("/task_status_timeout/{task_id}")
def get_task_status_with_timeout(
    *,
    db: Session = Depends(get_db),
    task_id: int,
    current_user: CurrentUserContext = Depends(get_current_user_with_token),
) -> Any:
    """
    Check the status of the API.
    Returns a JSON response indicating the service is working correctly.
    """

    try:
        user = current_user.user
        access_token = current_user.access_token

        result = service_vantage6.get_task_status_with_timeout(
            db=db, access_token=TOKEN_V6, task_id=task_id
        )
        logger.info("Status task for task_id=%s: %s", task_id, result)
        if not result:
            raise HTTPException(status_code=404, detail="No status for the task_id id")

        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
