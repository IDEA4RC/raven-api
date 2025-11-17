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
    cohort_query = Column(Text, nullable=True)
    creation_date = Column(DateTime(timezone=True), server_default=func.now())
    update_date = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    status = Column(Integer)  # Status of the cohort
    user_id = Column(Integer, ForeignKey("users.id"))
    analysis_id = Column(Integer, ForeignKey("analyses.id", ondelete="CASCADE"))
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"))
    
    # Relationships
    user = relationship("User")
    analysis = relationship("Analysis", back_populates="cohorts")
    workspace = relationship("Workspace", back_populates="cohorts")
    results = relationship("CohortResult", back_populates="cohort")
    algorithms = relationship("Algorithm", secondary="cohort_algorithms", back_populates="cohorts")
