from pydantic import BaseModel
from typing import Any, List, Dict


class DataPreparationRequest(BaseModel):
    workspace_id: int
    analysis_id: int
    cohorts_ids: List[int]


class V6TaskResult(BaseModel):
    task_id: int
    job_id: int


class V6GetStatus(BaseModel):
    task_id: int


class V6RunResult(BaseModel):
    status: str


class V6DecodedResult(BaseModel):
    task_id: int
    result: Dict[str, Any]
