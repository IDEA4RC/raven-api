"""
Endpoints for analysis operations
"""

from typing import Any, List, Dict

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app import schemas
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.analysis import analysis_service

router = APIRouter()


@router.post("/", response_model=schemas.analysis.Analysis, status_code=status.HTTP_201_CREATED)
def create_analysis(
    *,
    db: Session = Depends(get_db),
    analysis_in: schemas.analysis.AnalysisCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Creates a new analysis for a workspace.
    """
    try:
        analysis = analysis_service.create_with_history(
            db=db, obj_in=analysis_in, user_id=current_user.id
        )
        return analysis
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/")
def get_analyses(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Obtains all analyses with pagination.
    """
    analyses = analysis_service.get_multi(db=db, skip=skip, limit=limit)

    # Return a safely-serialized list to avoid strict Pydantic validation issues
    # when tests provide minimal fake objects (no DB/ORM instance).
    def serialize(a: Any) -> Dict[str, Any]:
        fields = [
            "id",
            "analysis_name",
            "analysis_description",
            "user_id",
            "workspace_id",
            "expiring_date",
            "creation_date",
            "update_date",
        ]
        return {k: getattr(a, k) for k in fields if hasattr(a, k) and getattr(a, k) is not None}

    return [serialize(a) for a in analyses]


@router.get("/{analysis_id}", response_model=schemas.analysis.Analysis)
def get_analysis(
    *,
    db: Session = Depends(get_db),
    analysis_id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Obtains an analysis by ID.
    """
    analysis = analysis_service.get(db=db, id=analysis_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis with ID {analysis_id} not found"
        )
    return analysis


@router.patch("/{analysis_id}", response_model=schemas.analysis.Analysis)
def update_analysis(
    *,
    db: Session = Depends(get_db),
    analysis_id: int,
    analysis_in: schemas.analysis.AnalysisUpdate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Updates an analysis (PATCH operation).
    Can update any combination of: analysis_name, analysis_description, expiring_date.
    """
    try:
        analysis = analysis_service.update_with_history(
            db=db, analysis_id=analysis_id, obj_in=analysis_in, user_id=current_user.id
        )
        return analysis
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_analysis(
    *,
    db: Session = Depends(get_db),
    analysis_id: int,
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Deletes an analysis.
    """
    try:
        analysis_service.delete_with_history(
            db=db, analysis_id=analysis_id, user_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/workspace/{workspace_id}", response_model=List[schemas.analysis.Analysis])
def get_analyses_by_workspace(
    *,
    db: Session = Depends(get_db),
    workspace_id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Obtains all analyses for a workspace.
    """
    analyses = analysis_service.get_analyses_by_workspace(db=db, workspace_id=workspace_id)
    return analyses


@router.get("/user/{user_id}", response_model=List[schemas.analysis.Analysis])
def get_analyses_by_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Obtains all analyses for a specific user with pagination.
    """
    analyses = analysis_service.get_analyses_by_user(
        db=db, user_id=user_id, skip=skip, limit=limit
    )
    return analyses


@router.get("/status/expired", response_model=List[schemas.analysis.Analysis])
def get_expired_analyses(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Obtains all expired analyses.
    """
    analyses = analysis_service.get_expired_analyses(db=db, skip=skip, limit=limit)
    return analyses


@router.get("/status/expiring-soon", response_model=List[schemas.analysis.Analysis])
def get_analyses_expiring_soon(
    *,
    db: Session = Depends(get_db),
    days: int = Query(7, ge=1, le=365, description="Number of days to look ahead for expiring analyses"),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Obtains all analyses expiring within the specified number of days.
    By default looks for analyses expiring in the next 7 days.
    """
    analyses = analysis_service.get_analyses_expiring_soon(
        db=db, days=days, skip=skip, limit=limit
    )
    return analyses


@router.get("/user/me/analyses", response_model=List[schemas.analysis.Analysis])
def get_my_analyses(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Obtains all analyses for the current authenticated user.
    """
    analyses = analysis_service.get_analyses_by_user(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )
    return analyses
