"""
Inicialización del paquete de servicios
"""

from app.services.permit import PermitService, permit_service
from app.services.workspace import WorkspaceService, workspace_service
from app.services.auth import AuthService, auth_service

__all__ = [
    "PermitService", "permit_service",
    "WorkspaceService", "workspace_service",
    "AuthService", "auth_service"
]
