"""
Schema de espacios de trabajo para validación de datos y serialización
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, field_validator


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

    @field_validator("team_ids", mode="before")
    @classmethod
    def clean_team_ids(cls, v):
        """Clean team_ids to remove invalid values like 'string'"""
        if not v:
            return []
        
        if isinstance(v, str):
            # If it's a single string, convert to list
            return [v] if v.strip() and v.strip() != "string" else []
        
        if isinstance(v, list):
            # Clean the list
            return [
                team_id.strip() for team_id in v 
                if team_id and isinstance(team_id, str) and team_id.strip() and team_id.strip() != "string"
            ]
        
        return []


class WorkspaceUpdate(BaseModel):
    """Schema para actualizar un espacio de trabajo."""
    name: Optional[str] = None
    description: Optional[str] = None
    data_access: Optional[int] = None
    update_date: Optional[datetime] = None
    team_ids: Optional[List[str]] = None

    @field_validator("team_ids", mode="before")
    @classmethod
    def clean_team_ids(cls, v):
        """Clean team_ids to remove invalid values like 'string'"""
        if not v:
            return None
        
        if isinstance(v, str):
            # If it's a single string, convert to list
            return [v] if v.strip() and v.strip() != "string" else []
        
        if isinstance(v, list):
            # Clean the list
            return [
                team_id.strip() for team_id in v 
                if team_id and isinstance(team_id, str) and team_id.strip() and team_id.strip() != "string"
            ]
        
        return None


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