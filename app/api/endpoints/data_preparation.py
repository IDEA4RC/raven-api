from fastapi import APIRouter, HTTPException
from app.services.vantage_6 import Vantage6Service
from app import schemas
import time
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db, get_current_user_with_token
from app.models.user import User
from app.api import CurrentUserContext
from app.utils.constants import TOKEN_V6
from typing import Any, List, Dict


router = APIRouter()

service = Vantage6Service()


@router.get("/", summary="Check API status")
async def data_preparation_check():
    """
    Check the status of the API.
    Returns a JSON response indicating the service is working correctly.
    """

    # This study is part of collaboration 2, and consists of UPM and IKNL

    return {
        "status": "ok",
        "message": "Data preparation works: The service is working correctly",
    }


@router.post(
    "/create_summary",
    response_model=schemas.V6TaskResult,
    status_code=status.HTTP_201_CREATED,
)
def create_data_preparation_summary(
    *,
    db: Session = Depends(get_db),
    data_preparation: schemas.DataPreparationRequest,
    current_user: CurrentUserContext = Depends(get_current_user_with_token),
) -> Any:
    """
    Check the status of the API.
    Returns a JSON response indicating the service is working correctly.
    """

    try:
        user = current_user.user
        access_token = current_user.access_token

        summary_task = service.data_preparation(
            db=db, access_token=TOKEN_V6, data_preparation_in=data_preparation
        )

        if not summary_task:
            raise HTTPException(
                status_code=404, detail="No cohorts found for the provided IDs"
            )

        return summary_task

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/status_task/{task_id}",
    response_model=schemas.V6RunResult,
    status_code=status.HTTP_200_OK,
)
def get_status_task(
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

        status_task = service.get_status_by_task_id(
            access_token=TOKEN_V6, task_id=task_id
        )

        if not status_task:
            raise HTTPException(status_code=404, detail="No status for the task id")

        return status_task

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/result_task/{task_id}", status_code=status.HTTP_200_OK)
def get_result_task(
    *,
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

        status_task = service.get_result_task_id(access_token=TOKEN_V6, task_id=task_id)

        if not status_task:
            raise HTTPException(status_code=404, detail="No status for the task id")

        return status_task

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/get_subtasks/{task_id}", status_code=status.HTTP_200_OK)
def get_subtasks(
    *,
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

        status_task = service.get_subtasks(access_token=TOKEN_V6, task_id=task_id)

        if not status_task:
            raise HTTPException(status_code=404, detail="No subtasks for the task id")

        return status_task

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/get_subtask_results/{task_id}", status_code=status.HTTP_200_OK)
def get_subtask_results(
    *,
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

        status_task = service.get_subtask_results(
            access_token=TOKEN_V6, subtask_id=task_id
        )

        if not status_task:
            raise HTTPException(
                status_code=404, detail="No subtask result for the task id"
            )

        return status_task

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
