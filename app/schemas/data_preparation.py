from pydantic import BaseModel, Field
from typing import Any, List, Dict, Optional, Union


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


class V6Variable(BaseModel):
    node_id: int
    name: str
    dtype: str


class V6Variables(BaseModel):
    variablesList: List[V6Variable]


class CrosstabPreparationRequest(BaseModel):
    workspace_id: int
    analysis_id: int
    cohorts_ids: List[int]
    variablesList: List[str]
    results_col: str
    group_cols: List[str] = Field(min_length=1)


class TTestRequest(BaseModel):
    workspace_id: int
    analysis_id: int
    cohorts_ids: List[int]


class BasicArithmeticRequest(BaseModel):
    dataframe_id: int
    column1: Union[str, int]
    column2: Union[str, int]
    operation: str
    output_column: str


class MergeCategoriesRequest(BaseModel):
    dataframe_id: int
    column: str
    output_column: str
    mapping: Dict[str, List[str]]


class TimedeltaRequest(BaseModel):
    dataframe_id: int
    column: str
    output_column: str


class OneHotEncodingRequest(BaseModel):
    dataframe_id: int
    column: str
    prefix: str


class KaplanMeierRequest(BaseModel):
    workspace_id: int
    analysis_id: int
    cohorts_ids: List[int]
    time_column_name: str
    censor_column_name: str
    strata_column_name: Optional[str] = None


class GLMRequest(BaseModel):
    workspace_id: int
    analysis_id: int
    cohorts_ids: List[int]
    family: str
    predictor_variables: List[str]
    outcome_variable: str


class MergeVariablesRequest(BaseModel):
    dataframe_id: int
    column1: str
    column2: str
    output_column: str
