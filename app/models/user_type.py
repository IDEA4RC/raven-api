"""
UserType model for the database
"""

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class UserType(Base):
    __tablename__ = "user_types"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text)
    metadata_search = Column(Integer)  # enum: none/view/edit/delete/create
    permissions = Column(Integer)  # enum: none/yes
    cohort_builder = Column(Integer)  # enum: none/yes
    data_quality = Column(Integer)  # enum: none/view/export
    export = Column(Integer)  # enum: none/view/edit/delete/export
    results_report = Column(Integer)  # enum: none/view/edit/export
    
    # Relationships
    users = relationship("User", back_populates="user_type")
