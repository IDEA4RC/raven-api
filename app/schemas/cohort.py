from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class CohortBase(BaseModel):
    """Base schema for cohorts."""
    cohort_name: str
    cohort_description: Optional[str] = None
    status: int

class CohortCreate(CohortBase):
    """Schema for creating a cohort."""
    workspace_id: int
    user_id: int
    status: Optional[int] = 0
    analysis_id: Optional[int] = None
    cohort_query: Optional[str] = None

class CohortStatusUpdate(BaseModel):
    """Schema for updating the status of a cohort."""
    status: int

class CohortUpdate(BaseModel):
    """Schema for updating a cohort."""
    cohort_name: Optional[str] = None
    cohort_description: Optional[str] = None
    cohort_query: Optional[str] = None
    status: Optional[int] = None
    
class Cohort(CohortBase):
    id: int
    cohort_name: str
    cohort_description: Optional[str] = None
    cohort_query: Optional[str] = None
    creation_date: datetime
    update_date: Optional[datetime] = None
    status: int
    user_id: int
    analysis_id: Optional[int] = None
    workspace_id: int
    
    model_config = ConfigDict(from_attributes=True)