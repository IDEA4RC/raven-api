"""
Permit model for the database
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, ARRAY
from sqlalchemy.orm import relationship

from app.models.base import Base


class Permit(Base):
    __tablename__ = "permits"

    id = Column(Integer, primary_key=True, index=True)
    permit_name = Column(String, index=True)
    creation_date = Column(DateTime(timezone=True), server_default=func.now())
    expiration_date = Column(DateTime(timezone=True))
    team_ids = Column(ARRAY(String), nullable=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    status = Column(Integer)  # enum: pending/iniciado/enviado/rechazado/concedido/expirado
    update_date = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    metadata_id = Column(Integer, ForeignKey("metadata_searches.id"), nullable=True)
    coes_granted = Column(ARRAY(String), nullable=True)  # Array of COEs granted when status is Granted
    
    # Relationships
    # team = relationship("Team", back_populates="permits")  # Removed: using team_ids array instead
    workspace = relationship("Workspace", back_populates="permits")
    metadata_search = relationship("MetadataSearch", back_populates="permits")