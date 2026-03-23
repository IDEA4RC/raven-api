from typing import Any, Optional
import json
import re

from pydantic import BaseModel, ConfigDict, field_validator


class CohortResultBase(BaseModel):
    """Base schema for cohort results."""

    cohort_id: int
    data_id: list[int]

    @field_validator("data_id", mode="before")
    @classmethod
    def normalize_data_id(cls, value: Any) -> list[int]:
        def flatten(v: Any) -> list[int]:
            if v is None:
                return []

            if isinstance(v, int):
                return [v]

            if isinstance(v, (list, tuple, set)):
                result: list[int] = []
                for item in v:
                    result.extend(flatten(item))
                return result

            if isinstance(v, str):
                raw = v.strip()
                if not raw:
                    return []

                if (raw.startswith("[") and raw.endswith("]")) or (
                    raw.startswith("{") and raw.endswith("}")
                ):
                    try:
                        decoded = json.loads(raw)
                        return flatten(decoded)
                    except json.JSONDecodeError:
                        pass

                numbers = re.findall(r"\d+", raw)
                return [int(n) for n in numbers]

            return flatten(str(v))

        normalized = flatten(value)
        if not normalized:
            raise ValueError("data_id must contain at least one integer value")

        # Preserve order, remove duplicates.
        return list(dict.fromkeys(normalized))


class CohortResultCreate(CohortResultBase):
    """Schema for creating a cohort result."""

    cohort_id: int
    data_id: list[int]


class CohortResultUpdate(BaseModel):
    """Schema for updating a cohort result."""

    data_id: Optional[list[int]] = None


class CohortResult(CohortResultBase):
    """Schema for reading a cohort result."""

    cohort_id: int
    data_id: list[int]

    model_config = ConfigDict(from_attributes=True)
