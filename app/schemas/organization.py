"""
Schema de organización para validación de datos y serialización
"""

from typing import Optional
from pydantic import BaseModel


class OrganizationBase(BaseModel):
    """Schema base para organizaciones."""
    name: str
    description: Optional[str] = None
    is_active: Optional[bool] = True


class OrganizationCreate(OrganizationBase):
    """Schema para crear una organización."""
    pass


class OrganizationUpdate(BaseModel):
    """Schema para actualizar una organización."""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class Organization(OrganizationBase):
    """Schema para leer una organización."""
    id: int
    
    class Config:
        """Configuración para el schema."""
        from_attributes = True
        from_attributes = True
