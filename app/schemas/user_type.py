"""
Schema de tipo de usuario para validación de datos y serialización
"""

from typing import Optional
from pydantic import BaseModel


class UserTypeBase(BaseModel):
    """Schema base para tipos de usuario."""
    name: str
    description: Optional[str] = None


class UserTypeCreate(UserTypeBase):
    """Schema para crear un tipo de usuario."""
    pass


class UserTypeUpdate(BaseModel):
    """Schema para actualizar un tipo de usuario."""
    name: Optional[str] = None
    description: Optional[str] = None


class UserType(UserTypeBase):
    """Schema para leer un tipo de usuario."""
    id: int
    
    class Config:
        """Configuración para el schema."""
        from_attributes = True
        from_attributes = True
