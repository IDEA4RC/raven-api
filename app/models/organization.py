"""
Organization model for the database
"""

from sqlalchemy import Boolean, Column, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    org_name = Column(String, index=True, nullable=False)
    description = Column(Text)
    org_city = Column(String)
    org_type = Column(Integer)  # enum: local/academic/industry
    data_available = Column(
        Boolean, default=False
    )  # New column to indicate data availability

    # Relationships
    users = relationship("User", back_populates="organization")
