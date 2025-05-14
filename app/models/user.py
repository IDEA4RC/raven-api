"""
User model for the database
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    keycloak_id = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    user_type_id = Column(Integer, ForeignKey("user_types.id"))
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    user_type = relationship("UserType", back_populates="users")
    teams = relationship("Team", secondary="user_teams", back_populates="users")
