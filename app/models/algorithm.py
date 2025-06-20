"""
Algorithm model for the database
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class Algorithm(Base):
    __tablename__ = "algorithms"

    id = Column(Integer, primary_key=True, index=True)
    method_name = Column(String, index=True)
    description = Column(Text)
    creation_date = Column(DateTime(timezone=True), server_default=func.now())
    version_date = Column(DateTime(timezone=True))
    input = Column(String)
    output = Column(String)
    analysis_id = Column(Integer, ForeignKey("analyses.id"))
    
    # Relationships
    analysis = relationship("Analysis", back_populates="algorithms")
    cohorts = relationship("Cohort", secondary="cohort_algorithms", back_populates="algorithms")
    cohort_algorithms = relationship("CohortAlgorithm", back_populates="algorithm")
