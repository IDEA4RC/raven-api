"""
User schema for data validation and serialization
"""

from typing import Optional
from pydantic import BaseModel, field_validator
import re


class UserBase(BaseModel):
    """Base schema for users."""
    email: str
    username: str
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, email: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
            raise ValueError("Invalid email format")
        return email
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = True


class UserCreate(UserBase):
    """Schema for creating a user."""
    keycloak_id: str  # ID provided by Keycloak
    organization_id: int
    user_type_id: int


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None
    user_type_id: Optional[int] = None


class UserInDB(UserBase):
    """Schema for reading a user from the database."""
    id: int
    keycloak_id: str
    organization_id: int
    user_type_id: int
    
    class Config:
        """Configuration for the schema."""
        from_attributes = True


class User(UserBase):
    """Schema for reading a user."""
    id: int
    keycloak_id: str
    organization_id: int
    user_type_id: int
    
    class Config:
        """Configuration for the schema."""
        from_attributes = True
