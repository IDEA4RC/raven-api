"""
MetadataSearch model for the database
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
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
    
    # Relationships
    workspace = relationship("Workspace", back_populates="metadata_searches")
