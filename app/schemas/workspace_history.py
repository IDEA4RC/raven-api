"""
Schema de historial de espacios de trabajo para validación de datos y serialización
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, ConfigDict


class WorkspaceHistoryBase(BaseModel):
    """Schema base para historial de espacios de trabajo."""
    date: datetime = None
    action: str
    description: Optional[str] = None


class WorkspaceHistoryCreate(WorkspaceHistoryBase):
    """Schema para crear un historial de espacio de trabajo."""
    user_id: int
    workspace_id: int


class WorkspaceHistory(WorkspaceHistoryBase):
    """Schema para leer un historial de espacio de trabajo."""
    id: int
    user_id: int
    workspace_id: int
    
    model_config = ConfigDict(from_attributes=True)