from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class AnalysisBase(BaseModel):
    """Base schema for analyses."""
    analysis_name: str
    analysis_description: Optional[str] = None
    user_id: int
    workspace_id: int
    expiring_date: Optional[datetime] = None
    creation_date: Optional[datetime] = None
    update_date: Optional[datetime] = None

class AnalysisCreate(BaseModel):
    """Schema for creating an analysis."""
    analysis_name: str
    analysis_description: Optional[str] = None
    user_id: int
    workspace_id: int
    expiring_date: Optional[datetime] = None

class AnalysisUpdate(BaseModel):
    """Schema for updating an analysis."""
    analysis_name: Optional[str] = None
    analysis_description: Optional[str] = None
    expiring_date: Optional[datetime] = None

class Analysis(AnalysisBase):
    """Schema for reading an analysis."""
    id: int
    analysis_name: str
    analysis_description: Optional[str] = None
    user_id: int
    workspace_id: int
    expiring_date: Optional[datetime] = None
    creation_date: Optional[datetime] = None
    update_date: Optional[datetime] = None


    model_config = ConfigDict(from_attributes=True)