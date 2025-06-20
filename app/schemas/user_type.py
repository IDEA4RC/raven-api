"""
User type schema for data validation and serialization
"""

from typing import Optional
from pydantic import BaseModel


class UserTypeBase(BaseModel):
    """Base schema for user types."""
    name: str
    description: Optional[str] = None


class UserTypeCreate(UserTypeBase):
    """Schema for creating a user type."""
    pass


class UserTypeUpdate(BaseModel):
    """Schema for updating a user type."""
    name: Optional[str] = None
    description: Optional[str] = None


class UserType(UserTypeBase):
    """Schema for reading a user type."""
    id: int
    
    class Config:
        """Configuration for the schema."""
        from_attributes = True
