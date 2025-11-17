"""
Endpoints for operations with workspaces
"""

from typing import Any, List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app import schemas
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.workspace import Workspace
from app.models.user_team import UserTeam
from app.services.workspace import workspace_service
from app.services.analysis import analysis_service
from app.models.analysis import Analysis

router = APIRouter()


@router.post("/", response_model=schemas.Workspace, status_code=status.HTTP_201_CREATED)
def create_workspace(
    *,
    db: Session = Depends(get_db),
    workspace_in: schemas.WorkspaceCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Creates a new workspace.
    """
    workspace = workspace_service.create_with_history(
        db=db, obj_in=workspace_in, user_id=current_user.id
    )
    return workspace


@router.get("/{workspace_id}", response_model=schemas.Workspace)
def get_workspace(
    *,
    db: Session = Depends(get_db),
    workspace_id: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Obtains a workspace by ID.
    """
    workspace = workspace_service.get(db=db, id=workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace with ID {workspace_id} not found"
        )
    return workspace


@router.get("/")
def get_workspaces(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[str] = Query(None, description="Filter by user_id (creator_id or team member)"),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Obtains the list of workspaces with optional filtering by user_id.
    Filters by: creator_id == user_id OR user_id is in any team that has access to the workspace.
    """
    # When no user filter is provided, delegate to the service which tests monkeypatch
    # to avoid hitting a real database/driver-specific features.
    if not user_id:
        workspaces = workspace_service.get_multi(db=db, skip=skip, limit=limit)
    else:
        # Preserve original filtering behavior when a user_id filter is provided
        try:
            user_id_int = int(user_id)
        except ValueError:
            return []

        # Build the filtered query; INFO: In production uses DB; in tests FakeSession returns empty
        query = db.query(Workspace)

        user_team_ids = [
            str(team_id[0]) for team_id in
            db.query(UserTeam.team_id).filter(UserTeam.user_id == user_id_int).all()
        ]

        creator_filter = Workspace.creator_id == user_id_int
        if user_team_ids:
            team_filter = Workspace.team_ids.op('&&')(user_team_ids)
            query = query.filter(or_(creator_filter, team_filter))
        else:
            query = query.filter(creator_filter)

        workspaces = query.offset(skip).limit(limit).all()

    def serialize(w: Any) -> Dict[str, Any]:
        fields = [
            "id",
            "name",
            "description",
            "version",
            "creation_date",
            "creator_id",
            "team_ids",
            "update_date",
            "metadata_search",
            "data_access",
            "data_analysis",
            "result_report",
            "v6_study_id",
            "status",
        ]
        return {k: getattr(w, k) for k in fields if hasattr(w, k) and getattr(w, k) is not None}

    return [serialize(w) for w in workspaces]


@router.delete("/{workspace_id}", status_code=status.HTTP_200_OK)
def delete_workspace(
    *,
    db: Session = Depends(get_db),
    workspace_id: int,
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Deletes a workspace by ID.
    """
    workspace = workspace_service.get(db=db, id=workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace with ID {workspace_id} not found"
        )
    
    # Check if user has permission to delete (could be creator or admin)
    if workspace.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this workspace"
        )
    
    #  Buscar todos los cohorts relacionados con este analysis
    analyses = db.query(Analysis).filter(Analysis.workspace_id == workspace_id).all()

    # 2️ Borrar los cohorts
    for analysis in analyses:
        analysis_service.delete_with_history_and_cohorts(db=db, analysis_id=analysis.id, user_id=current_user.id)
        
    deleted_workspace = workspace_service.remove(db=db, id=workspace_id)
    if not deleted_workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace with ID {workspace_id} not found"
        )
    return deleted_workspace


@router.patch("/{workspace_id}/data-access", response_model=schemas.Workspace)
def update_data_access(
    *,
    db: Session = Depends(get_db),
    workspace_id: int,
    data_access: int,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Updates the data access status of a workspace.
    """
    workspace = workspace_service.update_data_access(
        db=db, workspace_id=workspace_id, data_access=data_access, user_id=current_user.id
    )
    return workspace
