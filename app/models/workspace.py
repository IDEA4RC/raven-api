"""
Workspace model for the database
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text)
    version = Column(String)
    creation_date = Column(DateTime(timezone=True), server_default=func.utcnow())
    creator_id = Column(Integer, ForeignKey("users.id"))
    team_id = Column(Integer, ForeignKey("teams.id"))
    last_edit = Column(DateTime(timezone=True))
    metadata_search = Column(Integer)  # enum: pending/in_progress/completed
    data_access = Column(Integer)      # enum: pending/initiated/submitted/rejected/granted/expired
    data_query = Column(String)
    result_report = Column(Integer)    # enum: pending/in_progress/completed
    vr_study_id = Column(String)
    
    # Relationships
    creator = relationship("User", foreign_keys=[creator_id])
    team = relationship("Team", foreign_keys=[team_id])
    histories = relationship("WorkspaceHistory", back_populates="workspace")
    metadata_searches = relationship("MetadataSearch", back_populates="workspace")
    analyses = relationship("Analysis", back_populates="workspace")
    cohorts = relationship("Cohort", back_populates="workspace")
