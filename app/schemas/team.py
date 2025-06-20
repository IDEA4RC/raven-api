"""
Schema de equipo para validación de datos y serialización
"""

from typing import Optional
from pydantic import BaseModel


class TeamBase(BaseModel):
    """Schema base para equipos."""
    name: str
    description: Optional[str] = None
    is_active: Optional[bool] = True


class TeamCreate(TeamBase):
    """Schema para crear un equipo."""
    organization_id: int


class TeamUpdate(BaseModel):
    """Schema para actualizar un equipo."""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class Team(TeamBase):
    """Schema para leer un equipo."""
    id: int
    organization_id: int
    
    class Config:
        """Configuration for the schema."""
        from_attributes = True
        from_attributes = True
