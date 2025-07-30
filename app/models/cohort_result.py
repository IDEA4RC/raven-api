"""
CohortResult model for the database
"""

from sqlalchemy import Column, Integer, String, ForeignKey, ARRAY
from sqlalchemy.orm import relationship

from app.models.base import Base


class CohortResult(Base):
    __tablename__ = "cohort_results"

    data_id = Column(ARRAY(String), primary_key=True, index=True)
    cohort_id = Column(Integer, ForeignKey("cohorts.id"), primary_key=True)
    
    # Relationships
    cohort = relationship("Cohort", back_populates="results")
