"""
Permit model for the database
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class Permit(Base):
    __tablename__ = "permits"

    id = Column(Integer, primary_key=True, index=True)
    permit_name = Column(String, index=True)
    creation_date = Column(DateTime(timezone=True), server_default=func.utcnow())
    validity_date = Column(DateTime(timezone=True))
    team_id = Column(Integer, ForeignKey("teams.id"))
    status = Column(Integer)  # enum: pending/initiated/submitted/rejected/granted/canceled
    
    # Relationships
    team = relationship("Team", back_populates="permits")
