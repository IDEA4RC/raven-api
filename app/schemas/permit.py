"""
Schema de permisos para validación de datos y serialización
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class PermitBase(BaseModel):
    """Schema base para permisos."""
    status: int  # 0=Pending, 1=Iniciado, 2=Enviado, 3=Rechazado, 4=Concedido, 5=Expirado
    update_date: Optional[datetime] = None


class PermitCreate(PermitBase):
    """Schema para crear un permiso."""
    workspace_id: int
    permit_name: Optional[str] = None
    expiration_date: Optional[datetime] = None
    team_ids: Optional[List[str]] = None
    

class PermitUpdate(BaseModel):
    """Schema para actualizar un permiso."""
    status: int = None


class Permit(PermitBase):
    """Schema para leer un permiso."""
    id: int
    workspace_id: int
    permit_name: Optional[str] = None
    creation_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    team_ids: Optional[List[str]] = None
    
    model_config = ConfigDict(from_attributes=True)