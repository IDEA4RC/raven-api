"""Endpoints for organization operations."""

from typing import Any, List, Optional

from app.utils.constants import ORGANIZATION_DATA_AVAILABILITY
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import schemas
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.organization import organization_service

router = APIRouter()


@router.get("/", response_model=List[schemas.Organization])
def get_organizations(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get all organizations with pagination."""
    return organization_service.get_multi(db=db, skip=skip, limit=limit)


@router.get("/active_centers", response_model=List[schemas.Organization])
def get_organizations_filtered(
    *,
    db: Session = Depends(get_db),
    org_type: Optional[int] = None,
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get organizations filtered by org_type and/or data_available."""
    return organization_service.get_filtered(
        db=db,
        org_type=org_type,
        data_available=ORGANIZATION_DATA_AVAILABILITY.AVAILABLE,
    )


@router.get("/by_type_and_status", response_model=List[schemas.Organization])
def get_organizations_filtered(
    *,
    db: Session = Depends(get_db),
    org_type: Optional[int] = None,
    data_available: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get organizations filtered by org_type and/or data_available."""
    return organization_service.get_filtered(
        db=db,
        org_type=org_type,
        data_available=data_available,
    )
