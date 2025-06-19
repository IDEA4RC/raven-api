"""
Schema de espacios de trabajo para validación de datos y serialización
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class WorkspaceBase(BaseModel):
    """Schema base para espacios de trabajo."""
    name: str
    description: Optional[str] = None
    data_access: int  # 2 = Submitted según el diagrama
    last_edit: Optional[datetime] = None


class WorkspaceCreate(WorkspaceBase):
    """Schema para crear un espacio de trabajo."""
    team_ids: List[str]  # Changed from team_id to team_ids array


class WorkspaceUpdate(BaseModel):
    """Schema para actualizar un espacio de trabajo."""
    name: Optional[str] = None
    description: Optional[str] = None
    data_access: Optional[int] = None
    last_edit: Optional[datetime] = None
    team_ids: Optional[List[str]] = None


class Workspace(WorkspaceBase):
    """Schema para leer un espacio de trabajo."""
    id: int
    creator_id: int
    team_ids: List[str]  # Changed from team_id to team_ids array
    
    class Config:
        """Configuración para el schema."""
        orm_mode = True
        from_attributes = True