"""
Example endpoints used in tests.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel


router = APIRouter()


class Example(BaseModel):
    id: int | None = None
    name: str
    description: str | None = None


_EXAMPLES_DB: Dict[int, Example] = {}
_SEQ: int = 1


@router.get("/", response_model=List[Example])
def list_examples() -> List[Example]:
    return list(_EXAMPLES_DB.values())


@router.post("/", response_model=Example, status_code=status.HTTP_201_CREATED)
def create_example(example: Example) -> Example:
    global _SEQ
    new = Example(id=_SEQ, name=example.name, description=example.description)
    _EXAMPLES_DB[_SEQ] = new
    _SEQ += 1
    return new


@router.get("/{example_id}", response_model=Example)
def get_example(example_id: int) -> Example:
    ex = _EXAMPLES_DB.get(example_id)
    if not ex:
        raise HTTPException(status_code=404, detail="Example not found")
    return ex
