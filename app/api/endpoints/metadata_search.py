"""
Endpoints to check the service status
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import any_

from app import schemas
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.metadata_search import MetadataSearch
from app.services.metadata_search import metadata_search_service

router = APIRouter()


@router.get("/", summary="Check API status")
async def metadata_search():
    """
    Check the status of the API.
    Returns a JSON response indicating the service is working correctly.
    """
    return {"status": "ok", "message": "The service is working correctly"}

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
