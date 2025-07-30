"""
Endpoints for cohort result operations
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session

from app import schemas
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.cohort_result import cohort_result_service

router = APIRouter()


@router.post("/", response_model=schemas.cohort_result.CohortResult, status_code=status.HTTP_201_CREATED)
def create_cohort_result(
    *,
    db: Session = Depends(get_db),
    cohort_result_in: schemas.cohort_result.CohortResultCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Creates a new cohort result.
    """
    try:
        cohort_result = cohort_result_service.create_for_cohort(
            db=db, obj_in=cohort_result_in
        )
        return cohort_result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/cohort/{cohort_id}", response_model=List[schemas.cohort_result.CohortResult])
def get_cohort_results_by_cohort(
    *,
    db: Session = Depends(get_db),
    cohort_id: int = Path(..., description="ID of the cohort"),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Gets all cohort results for a specific cohort with pagination.
    """
    cohort_results = cohort_result_service.get_by_cohort(
        db=db, cohort_id=cohort_id, skip=skip, limit=limit
    )
    return cohort_results


@router.get("/cohort/{cohort_id}/data-ids", response_model=List[List[str]])
def get_data_ids_for_cohort(
    *,
    db: Session = Depends(get_db),
    cohort_id: int = Path(..., description="ID of the cohort"),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Gets all data_ids for a specific cohort.
    """
    try:
        data_ids = cohort_result_service.get_data_ids_for_cohort(
            db=db, cohort_id=cohort_id
        )
        return data_ids
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/cohort/{cohort_id}/count", response_model=int)
def count_cohort_results(
    *,
    db: Session = Depends(get_db),
    cohort_id: int = Path(..., description="ID of the cohort"),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Counts the number of results for a specific cohort.
    """
    count = cohort_result_service.count_results_for_cohort(
        db=db, cohort_id=cohort_id
    )
    return count


@router.patch("/cohort/{cohort_id}/data-id", response_model=schemas.cohort_result.CohortResult)
def update_cohort_result(
    *,
    db: Session = Depends(get_db),
    cohort_id: int = Path(..., description="ID of the cohort"),
    cohort_result_in: schemas.cohort_result.CohortResultUpdate,
    current_data_id: List[str],
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Updates a cohort result by cohort_id and current data_id.
    You need to provide the current data_id in the request body to identify which record to update.
    """
    try:
        cohort_result = cohort_result_service.update_cohort_result(
            db=db, 
            cohort_id=cohort_id, 
            data_id=current_data_id, 
            obj_in=cohort_result_in
        )
        return cohort_result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/cohort/{cohort_id}/data-id", status_code=status.HTTP_204_NO_CONTENT)
def delete_cohort_result(
    *,
    db: Session = Depends(get_db),
    cohort_id: int = Path(..., description="ID of the cohort"),
    data_id_to_delete: List[str],
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Deletes a specific cohort result by cohort_id and data_id.
    You need to provide the data_id in the request body to identify which record to delete.
    """
    try:
        cohort_result_service.delete_cohort_result(
            db=db, cohort_id=cohort_id, data_id=data_id_to_delete
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/cohort/{cohort_id}/all", response_model=dict)
def delete_all_cohort_results(
    *,
    db: Session = Depends(get_db),
    cohort_id: int = Path(..., description="ID of the cohort"),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Deletes all cohort results for a specific cohort.
    Returns the number of deleted records.
    """
    try:
        deleted_count = cohort_result_service.delete_all_for_cohort(
            db=db, cohort_id=cohort_id
        )
        return {"deleted_count": deleted_count, "message": f"Deleted {deleted_count} cohort results"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/cohort/{cohort_id}/bulk", response_model=List[schemas.cohort_result.CohortResult])
def bulk_create_cohort_results(
    *,
    db: Session = Depends(get_db),
    cohort_id: int = Path(..., description="ID of the cohort"),
    data_ids: List[List[str]],
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Creates multiple cohort results for a cohort in a single transaction.
    Skips any data_ids that already exist for the cohort.
    """
    try:
        cohort_results = cohort_result_service.bulk_create_for_cohort(
            db=db, cohort_id=cohort_id, data_ids=data_ids
        )
        return cohort_results
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
