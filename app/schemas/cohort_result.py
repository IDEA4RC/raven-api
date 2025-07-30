from typing import Optional
from pydantic import BaseModel, ConfigDict


class CohortResultBase(BaseModel):
    """Base schema for cohort results."""
    cohort_id: int
    data_id: list[str]  # Assuming data_id is a list of strings

class CohortResultCreate(CohortResultBase):
    """Schema for creating a cohort result."""
    cohort_id: int
    data_id: list[str]

class CohortResultUpdate(BaseModel):
    """Schema for updating a cohort result."""
    data_id: Optional[list[str]] = None

class CohortResult(CohortResultBase):
    """Schema for reading a cohort result."""
    cohort_id: int
    data_id: list[str]
    
    model_config = ConfigDict(from_attributes=True)