from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class AlgorithmBase(BaseModel):
    """Base schema for algorithms."""

    method_name: str
    description: Optional[str] = None
    input: Optional[str] = None
    dataframe_vantage_id: Optional[int] = None
    task_id: int = None


class AlgorithmCreate(AlgorithmBase):
    cohort_ids: List[int]


class AlgorithmUpdate(BaseModel):
    method_name: Optional[str] = None
    description: Optional[str] = None
    input: Optional[str] = None
    output: Optional[str] = None
    task_id: int
    subtask_id: Optional[int] = None
    status_task: Optional[str] = None
    status_subtask: Optional[str] = None
    version_date: Optional[datetime] = None


class Algorithm(AlgorithmBase):
    id: int
    creation_date: datetime
    version_date: Optional[datetime]
    cohort_ids: List[int] = []
    status_task: Optional[str]
    subtask_id: Optional[int]
    status_subtask: Optional[str]
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm(cls, obj):
        """Extiende from_orm para incluir los cohort_ids."""
        alg = super().from_orm(obj)
        alg.cohort_ids = [c.id for c in getattr(obj, "cohorts", [])]
        return alg
