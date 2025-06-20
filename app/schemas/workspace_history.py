"""
Schema de historial de espacios de trabajo para validación de datos y serialización
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class WorkspaceHistoryBase(BaseModel):
    """Schema base para historial de espacios de trabajo."""
    date: datetime = None
    action: str  # "Submitted data access application"
    phase: str  # "Data Permit"
    details: Optional[str] = None  # "The data permit application has been submitted"


class WorkspaceHistoryCreate(WorkspaceHistoryBase):
    """Schema para crear un historial de espacio de trabajo."""
    creator_id: int
    workspace_id: int


class WorkspaceHistory(WorkspaceHistoryBase):
    """Schema para leer un historial de espacio de trabajo."""
    id: int
    creator_id: int
    workspace_id: int
    
    class Config:
        """Configuration for the schema."""
        from_attributes = True
        from_attributes = True