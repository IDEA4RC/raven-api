from pydantic import BaseModel

class DataPreparationRequest(BaseModel):
    session_id: int
    study_id: int


class V6TaskResult(BaseModel):
    task_id: int


class V6RunResult(BaseModel):
    status: str