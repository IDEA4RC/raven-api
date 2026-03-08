from pydantic import BaseModel
from typing import List


class CohortListRequest(BaseModel):
    cohort_ids: List[int]
