"""Organization schemas."""

from typing import Optional

from pydantic import BaseModel, ConfigDict


class OrganizationBase(BaseModel):
    """Base schema for organizations."""

    org_name: str
    description: Optional[str] = None
    org_city: Optional[str] = None
    org_type: Optional[int] = None
    data_available: bool = False


class OrganizationCreate(OrganizationBase):
    """Schema for creating an organization."""

    pass


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""

    org_name: Optional[str] = None
    description: Optional[str] = None
    org_city: Optional[str] = None
    org_type: Optional[int] = None
    data_available: Optional[bool] = None


class Organization(OrganizationBase):
    """Schema for reading an organization."""

    id: int

    model_config = ConfigDict(from_attributes=True)
