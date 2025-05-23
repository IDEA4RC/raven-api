"""
Permit model for the database
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import Base


class Permit(Base):
    __tablename__ = "permits"

    id = Column(Integer, primary_key=True, index=True)
    permit_name = Column(String, index=True)
    creation_date = Column(DateTime(timezone=True), default=datetime.utcnow)
    validity_date = Column(DateTime(timezone=True))
    team_id = Column(Integer, ForeignKey("teams.id"))
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    status = Column(Integer)  # enum: pending/initiated/submitted/rejected/granted/canceled
    update_date = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    team = relationship("Team", back_populates="permits")
    workspace = relationship("Workspace", back_populates="permits")
    
    # Relationships
    team = relationship("Team", back_populates="permits")
