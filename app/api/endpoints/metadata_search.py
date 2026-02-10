"""
Endpoints to check the service status
"""

from typing import Any, List

from app.models.permit import Permit
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import any_

from app import schemas
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.metadata_search import metadata_search_service
from sqlalchemy.exc import NoResultFound, MultipleResultsFound
router = APIRouter()


@router.get("/", summary="Check API status")
async def metadata_search():
    """
    Check the status of the API.
    Returns a JSON response indicating the service is working correctly.
    """
    return {"status": "ok", "message": "The service is working correctly"}

@router.get("/workspace/{workspace_id}", response_model=schemas.MetadataSearch)
def get_permits_by_workspace(
    *,
    db: Session = Depends(get_db),
    workspace_id: int,
) -> Any:
    """
    Obtains all permits for a workspace.
    """
    try:
        return metadata_search_service.get_metadata_search_by_workspace(
        db=db,
        workspace_id=workspace_id,
        )
    except NoResultFound:
        raise HTTPException(
        status_code=404,
        detail="Metadata search not found for workspace",
        )
    except MultipleResultsFound:
        raise HTTPException(
        status_code=500,
        detail="Multiple metadata records found for workspace",
        )
