"""
Cohort model for the database
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class Cohort(Base):
    __tablename__ = "cohorts"

    id = Column(Integer, primary_key=True, index=True)
    cohort_name = Column(String, index=True)
    cohort_description = Column(Text)
    creation_date = Column(DateTime(timezone=True), server_default=func.now())
    version_date = Column(DateTime(timezone=True))
    status = Column(Integer)  # Status of the cohort
    user_id = Column(Integer, ForeignKey("users.id"))
    analysis_id = Column(Integer, ForeignKey("analyses.id"))
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    
    # Relationships
    user = relationship("User")
    analysis = relationship("Analysis", back_populates="cohorts")
    workspace = relationship("Workspace", back_populates="cohorts")
    results = relationship("CohortResult", back_populates="cohort")
    algorithms = relationship("Algorithm", secondary="cohort_algorithms", back_populates="cohorts")
