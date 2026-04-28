"""
CohortResult model for the database
"""

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base


class CohortResult(Base):
    __tablename__ = "cohort_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    data_id = Column(JSONB, nullable=False, server_default="[]")
    cohort_id = Column(Integer, ForeignKey("cohorts.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    cohort = relationship("Cohort", back_populates="results")
