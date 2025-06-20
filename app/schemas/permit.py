"""
Schema de permisos para validación de datos y serialización
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class PermitBase(BaseModel):
    """Schema base para permisos."""
    status: int  # 2 = Submitted according to diagram
    update_date: datetime = None


class PermitCreate(PermitBase):
    """Schema para crear un permiso."""
    workspace_id: int
    

class PermitUpdate(BaseModel):
    """Schema para actualizar un permiso."""
    status: Optional[int] = None
    update_date: Optional[datetime] = None


class Permit(PermitBase):
    """Schema para leer un permiso."""
    id: int
    workspace_id: int
    
    class Config:
        """Configuration for the schema."""
        from_attributes = True
        from_attributes = True