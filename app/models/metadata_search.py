"""
MetadataSearch model for the database
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, ARRAY, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class MetadataSearch(Base):
    __tablename__ = "metadata_searches"

    id = Column(Integer, primary_key=True, index=True)
    update_date = Column(DateTime(timezone=True), onupdate=func.now())
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    shared = Column(String)  # For sharing configuration
    type_cancer = Column(String)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    status = Column(String)

    id_variables = Column(ARRAY(Text), default=list)
    selected_id_coes = Column(ARRAY(Text), default=list)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="metadata_searches")
    permits = relationship("Permit", back_populates="metadata_search")
