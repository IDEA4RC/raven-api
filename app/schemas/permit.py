"""
Schema de permisos para validación de datos y serialización
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class PermitBase(BaseModel):
    """Schema base para permisos."""
    status: int  # 1=Pending, 2=Submitted, 3=Approved, 4=Rejected, etc.
    update_date: Optional[datetime] = None


class PermitCreate(PermitBase):
    """Schema para crear un permiso."""
    workspace_id: int
    permit_name: Optional[str] = None
    validity_date: Optional[datetime] = None
    team_id: Optional[int] = None
    

class PermitUpdate(BaseModel):
    """Schema para actualizar un permiso."""
    status: Optional[int] = None
    update_date: Optional[datetime] = None
    permit_name: Optional[str] = None
    validity_date: Optional[datetime] = None
    team_id: Optional[int] = None
    user_teams_ids: Optional[List[str]] = None  # Campo para los IDs de equipos de usuario


class Permit(PermitBase):
    """Schema para leer un permiso."""
    id: int
    workspace_id: int
    permit_name: Optional[str] = None
    creation_date: Optional[datetime] = None
    validity_date: Optional[datetime] = None
    team_id: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)