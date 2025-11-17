"""
CohortResult model for the database
"""

from sqlalchemy import Column, Integer, ForeignKey, ARRAY, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class CohortResult(Base):
    __tablename__ = "cohort_results"

    # Almacenamos ahora un array de texto (text[]) para permitir múltiples IDs flexibles.
    # Usamos Text en lugar de String para evitar longitud y la mención a VARCHAR/VARYING.
   
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    data_id = Column(ARRAY(Text), nullable=False)
    cohort_id = Column(Integer, ForeignKey("cohorts.id", ondelete="CASCADE"), nullable=False)   
    
    # Relationships
    cohort = relationship("Cohort", back_populates="results")
