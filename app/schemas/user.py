"""
Schema de usuario para validación de datos y serialización
"""

from typing import Optional
from pydantic import BaseModel, field_validator
import re


class UserBase(BaseModel):
    """Schema base para usuarios."""
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
    """Schema para crear un usuario."""
    keycloak_id: str  # ID proporcionado por Keycloak
    organization_id: int
    user_type_id: int


class UserUpdate(BaseModel):
    """Schema para actualizar un usuario."""
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None
    user_type_id: Optional[int] = None


class UserInDB(UserBase):
    """Schema para leer un usuario de la base de datos."""
    id: int
    keycloak_id: str
    organization_id: int
    user_type_id: int
    
    class Config:
        """Configuración para el schema."""
        from_attributes = True


class User(UserBase):
    """Schema para leer un usuario."""
    id: int
    keycloak_id: str
    organization_id: int
    user_type_id: int
    
    class Config:
        """Configuración para el schema."""
        from_attributes = True
