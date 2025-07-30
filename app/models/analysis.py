"""
Analysis model for the database
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    analysis_name = Column(String, index=True)
    analysis_description = Column(Text)
    creation_date = Column(DateTime(timezone=True), server_default=func.now())
    update_date = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    user_id = Column(Integer, ForeignKey("users.id"))
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    expiring_date = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User")
    workspace = relationship("Workspace", back_populates="analyses")
    algorithms = relationship("Algorithm", back_populates="analysis")
    cohorts = relationship("Cohort", back_populates="analysis")
