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


@router.get("/get_variables_dataframe/{dataframe_id}", status_code=status.HTTP_200_OK)
def get_variables_dataframe(
    *,
    dataframe_id: int,
    current_user: CurrentUserContext = Depends(get_current_user_with_token),
) -> Any:
    """
    Check the status of the API.
    Returns a JSON response indicating the service is working correctly.
    """

    try:
        user = current_user.user
        access_token = current_user.access_token

        status_task = service.get_variables_dataframe(
            access_token=TOKEN_V6, dataframe_id=dataframe_id
        )

        if not status_task:
            raise HTTPException(
                status_code=404, detail="No variables found for the dataframe id"
            )

        return status_task

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


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


@router.post(
    "/create_crosstab",
    response_model=schemas.V6TaskResult,
    status_code=status.HTTP_201_CREATED,
)
def create_data_preparation_crosstab(
    *,
    db: Session = Depends(get_db),
    crosstab_preparation_data: schemas.CrosstabPreparationRequest,
    current_user: CurrentUserContext = Depends(get_current_user_with_token),
) -> Any:
    """
    Check the status of the API.
    Returns a JSON response indicating the service is working correctly.
    """

    try:
        user = current_user.user
        access_token = current_user.access_token

        summary_task = service.create_crosstab(
            db=db,
            access_token=TOKEN_V6,
            crosstab_preparation_in=crosstab_preparation_data,
        )

        if not summary_task:
            raise HTTPException(
                status_code=404, detail="No cohorts found for the provided IDs"
            )

        return summary_task

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/create_coxph",
    response_model=schemas.V6TaskResult,
    status_code=status.HTTP_201_CREATED,
)
def create_coxph(
    *,
    db: Session = Depends(get_db),
    coxph_data: schemas.CoxPHRequest,
    current_user: CurrentUserContext = Depends(get_current_user_with_token),
) -> Any:
    """
    Create a Cox Proportional Hazards (CoxPH) analytics task in Vantage6.
    Returns task_id and job_id for polling.
    """
    try:
        result = service.create_coxph(
            db=db,
            access_token=TOKEN_V6,
            coxph_in=coxph_data,
        )

        if not result:
            raise HTTPException(
                status_code=404, detail="No cohorts found for the provided IDs"
            )

        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/create_glm",
    response_model=schemas.V6TaskResult,
    status_code=status.HTTP_201_CREATED,
)
def create_glm(
    *,
    db: Session = Depends(get_db),
    glm_data: schemas.GLMRequest,
    current_user: CurrentUserContext = Depends(get_current_user_with_token),
) -> Any:
    """
    Create a Generalized Linear Model (GLM) analytics task in Vantage6.
    Returns task_id and job_id for polling.
    """
    try:
        result = service.create_glm(
            db=db,
            access_token=TOKEN_V6,
            glm_in=glm_data,
        )

        if not result:
            raise HTTPException(
                status_code=404, detail="No cohorts found for the provided IDs"
            )

        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/create_kaplan_meier",
    response_model=schemas.V6TaskResult,
    status_code=status.HTTP_201_CREATED,
)
def create_kaplan_meier(
    *,
    db: Session = Depends(get_db),
    km_data: schemas.KaplanMeierRequest,
    current_user: CurrentUserContext = Depends(get_current_user_with_token),
) -> Any:
    """
    Create a Kaplan-Meier survival analysis task in Vantage6.
    Returns both the KM estimate and Log-Rank test results.
    Returns task_id and job_id for polling.
    """

    try:
        user = current_user.user
        access_token = current_user.access_token

        result = service.create_kaplan_meier(
            db=db,
            access_token=TOKEN_V6,
            km_in=km_data,
        )

        if not result:
            raise HTTPException(
                status_code=404, detail="No cohorts found for the provided IDs"
            )

        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/create_t_test",
    response_model=schemas.V6TaskResult,
    status_code=status.HTTP_201_CREATED,
)
def create_data_preparation_t_test(
    *,
    db: Session = Depends(get_db),
    t_test_data: schemas.TTestRequest,
    current_user: CurrentUserContext = Depends(get_current_user_with_token),
) -> Any:
    """
    Create a t-test task in Vantage6.
    Returns task_id and job_id for polling.
    """

    try:
        user = current_user.user
        access_token = current_user.access_token

        t_test_task = service.create_t_test(
            db=db,
            access_token=TOKEN_V6,
            t_test_in=t_test_data,
        )

        if not t_test_task:
            raise HTTPException(
                status_code=404, detail="No cohorts found for the provided IDs"
            )

        return t_test_task

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


@router.post(
    "/create_basic_arithmetic",
    response_model=schemas.V6TaskResult,
    status_code=status.HTTP_201_CREATED,
)
def create_basic_arithmetic(
    *,
    basic_arithmetic_data: schemas.BasicArithmeticRequest,
    current_user: CurrentUserContext = Depends(get_current_user_with_token),
) -> Any:
    """
    Create a basic arithmetic preprocessing task in Vantage6.
    Modifies the specified dataframe by computing a new column from two operands.
    Returns task_id and job_id for polling.
    """

    try:
        user = current_user.user
        access_token = current_user.access_token

        result = service.create_basic_arithmetic(
            access_token=TOKEN_V6,
            basic_arithmetic_in=basic_arithmetic_data,
        )

        if not result:
            raise HTTPException(
                status_code=404, detail="No result from Vantage6 preprocessing"
            )

        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/create_merge_categories",
    response_model=schemas.V6TaskResult,
    status_code=status.HTTP_201_CREATED,
)
def create_merge_categories(
    *,
    merge_categories_data: schemas.MergeCategoriesRequest,
    current_user: CurrentUserContext = Depends(get_current_user_with_token),
) -> Any:
    """
    Create a merge_categories preprocessing task in Vantage6.
    Remaps categories of an existing column into a new output column.
    Returns task_id and job_id for polling.
    """

    try:
        user = current_user.user
        access_token = current_user.access_token

        result = service.create_merge_categories(
            access_token=TOKEN_V6,
            merge_categories_in=merge_categories_data,
        )

        if not result:
            raise HTTPException(
                status_code=404, detail="No result from Vantage6 preprocessing"
            )

        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/create_one_hot_encoding",
    response_model=schemas.V6TaskResult,
    status_code=status.HTTP_201_CREATED,
)
def create_one_hot_encoding(
    *,
    one_hot_encoding_data: schemas.OneHotEncodingRequest,
    current_user: CurrentUserContext = Depends(get_current_user_with_token),
) -> Any:
    """
    Create a one_hot_encode preprocessing task in Vantage6.
    Creates a binary column for each category in the specified column using the given prefix.
    Returns task_id and job_id for polling.
    """

    try:
        user = current_user.user
        access_token = current_user.access_token

        result = service.create_one_hot_encoding(
            access_token=TOKEN_V6,
            one_hot_encoding_in=one_hot_encoding_data,
        )

        if not result:
            raise HTTPException(
                status_code=404, detail="No result from Vantage6 preprocessing"
            )

        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/create_merge_variables",
    response_model=schemas.V6TaskResult,
    status_code=status.HTTP_201_CREATED,
)
def create_merge_variables(
    *,
    merge_variables_data: schemas.MergeVariablesRequest,
    current_user: CurrentUserContext = Depends(get_current_user_with_token),
) -> Any:
    """
    Create a merge_variables preprocessing task in Vantage6.
    Concatenates two columns into a new output column.
    Returns task_id and job_id for polling.
    """
    try:
        result = service.create_merge_variables(
            access_token=TOKEN_V6,
            merge_variables_in=merge_variables_data,
        )

        if not result:
            raise HTTPException(status_code=404, detail="merge_variables task failed")

        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/create_timedelta",
    response_model=schemas.V6TaskResult,
    status_code=status.HTTP_201_CREATED,
)
def create_timedelta(
    *,
    timedelta_data: schemas.TimedeltaRequest,
    current_user: CurrentUserContext = Depends(get_current_user_with_token),
) -> Any:
    """
    Create a timedelta preprocessing task in Vantage6.
    Computes the number of days from a date column to today and stores it in output_column.
    Returns task_id and job_id for polling.
    """

    try:
        user = current_user.user
        access_token = current_user.access_token

        result = service.create_timedelta(
            access_token=TOKEN_V6,
            timedelta_in=timedelta_data,
        )

        if not result:
            raise HTTPException(
                status_code=404, detail="No result from Vantage6 preprocessing"
            )

        return result

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
