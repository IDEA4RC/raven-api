"""Service for organization operations."""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate, OrganizationUpdate
from app.services.base import BaseService


class OrganizationService(
    BaseService[Organization, OrganizationCreate, OrganizationUpdate]
):
    def __init__(self) -> None:
        super().__init__(Organization)

    def get_filtered(
        self,
        db: Session,
        *,
        org_type: Optional[int] = None,
        data_available: Optional[bool] = None,
    ) -> List[Organization]:
        query = db.query(self.model)

        if org_type is not None:
            query = query.filter(self.model.org_type == org_type)

        if data_available is not None:
            query = query.filter(self.model.data_available == data_available)

        return query.all()


organization_service = OrganizationService()
