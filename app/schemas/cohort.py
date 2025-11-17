from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class CohortBase(BaseModel):
    """Base schema for cohorts."""
    cohort_name: str
    cohort_description: Optional[str] = None
    status: int
    workspace_id: int
    creation_date: Optional[datetime] = None
    update_date: Optional[datetime] = None
    analysis_id: int


class CohortCreate(CohortBase):
    """Schema for creating a cohort."""
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
    cohort_query: Optional[str] = None
    user_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)