from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class MetadataSearchBase(BaseModel):
    workspace_id: int
    type_cancer: str    
    status: str
    update_date: Optional[datetime] = None
    creation_date: Optional[datetime] = None

class MetadataSearchCreate(MetadataSearchBase):
    pass  # ya hereda todos los campos necesarios

class MetadataSearchUpdate(MetadataSearchBase):
    id_variables:  Optional[List[str]] = None
    selected_id_coes: Optional[List[str]] = None

class MetadataSearch(MetadataSearchBase):
    """Schema for reading an analysis."""
    id: int
    created_date: datetime
    update_date: datetime
    shared: Optional[str] = None
    type_cancer: str
    workspace_id: int 
    status: str
    id_variables: Optional[List[str]]
    selected_id_coes: Optional[List[str]]


    class Config:
        """Configuration for the schema."""
        from_attributes = True