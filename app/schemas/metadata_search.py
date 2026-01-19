"""
Schema de permisos para validación de datos y serialización
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class MetadataSearch(BaseModel):
    session_id: int
    study_id: int