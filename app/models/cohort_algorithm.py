"""
CohortAlgorithm model for the database
"""

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import Base


class CohortAlgorithm(Base):
    __tablename__ = "cohort_algorithms"

    cohort_id = Column(Integer, ForeignKey("cohorts.id"), primary_key=True)
    algorithm_id = Column(Integer, ForeignKey("algorithms.id"), primary_key=True)
    
    # Relationships
    algorithm = relationship("Algorithm", back_populates="cohort_algorithms")
