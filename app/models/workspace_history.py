"""
WorkspaceHistory model for the database
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base


class WorkspaceHistory(Base):
    __tablename__ = "workspace_histories"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime(timezone=True), default=func.now())
    phase = Column(String, nullable=False)
    action = Column(String)
    description = Column(String)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    creator_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    workspace = relationship("Workspace", back_populates="histories")
    creator = relationship("User", foreign_keys=[creator_id])
