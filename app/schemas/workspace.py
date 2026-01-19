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
    data_access: int  # 2 = Submitted according to diagram
    update_date: Optional[datetime] = None


class WorkspaceCreate(WorkspaceBase):
    """Schema para crear un espacio de trabajo."""
    team_ids: List[str]  # Changed from team_id to team_ids array
    metadata_search: int = 0  # enum: pending/in_progress/completed
    data_access: int = 0  # enum: pending/initiated/submitted/rejected/granted/expired
    data_analysis: int = 0  # enum: pending/in_progress/completed
    result_report: int = 0
    v6_study_id: Optional[str] = None
    status: Optional[str] = None  # Optional field for status

class WorkspaceCreateV2(WorkspaceBase):
    """Schema para crear un espacio de trabajo."""
    team_ids: List[str]  # Changed from team_id to team_ids array
    metadata_search: int = 0  # enum: pending/in_progress/completed
    data_access: int = 0  # enum: pending/initiated/submitted/rejected/granted/expired
    data_analysis: int = 0  # enum: pending/in_progress/completed
    result_report: int = 0
    v6_study_id: Optional[str] = None
    status: Optional[str] = None  # Optional field for status
    id_variables: List[str]   # New field for id_variables
    selected_id_coes: List[str]  # New field for selected_id_coes
    type_cancer: str   # New field for type_cancer


class WorkspaceUpdate(BaseModel):
    """Schema para actualizar un espacio de trabajo."""
    name: Optional[str] = None
    description: Optional[str] = None
    data_access: Optional[int] = None
    update_date: Optional[datetime] = None
    team_ids: Optional[List[str]] = None


class Workspace(WorkspaceBase):
    """Schema para leer un espacio de trabajo."""
    id: int
    creator_id: int
    team_ids: List[str]  # Changed from team_id to team_ids array
    creation_date: datetime
    metadata_search: int  # enum: pending/in_progress/completed
    data_analysis: int  # enum: pending/in_progress/completed
    result_report: int  # enum: pending/in_progress/completed
    v6_study_id: Optional[str] = None
    status: Optional[str] = None  # Optional field for status
    
    class Config:
        """Configuration for the schema."""
        from_attributes = True