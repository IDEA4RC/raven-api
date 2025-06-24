"""
Team model for the database
"""

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    team_name = Column(String, index=True, nullable=False)
    team_contact_name = Column(String)
    address = Column(Text)
    
    # Relationships
    users = relationship("User", secondary="user_teams", back_populates="teams")
    # permits = relationship("Permit", back_populates="team")  # Removed: using team_ids array instead
    # Note: workspaces relationship removed since we now use team_ids array in Workspace
