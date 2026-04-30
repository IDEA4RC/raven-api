from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class ExecutionEntry(BaseModel):
    execution_date: str
    patient_ids: List[Any]


class CohortResultCreate(BaseModel):
    cohort_id: int
    # {"<coe_token>": [{"execution_date": "...", "patient_ids": [...]}]}
    data_id: Dict[str, List[ExecutionEntry]]


class CohortResultUpdate(BaseModel):
    data_id: Optional[Any] = None


class CohortResult(BaseModel):
    id: int
    cohort_id: int
    data_id: Any

    model_config = ConfigDict(from_attributes=True)
