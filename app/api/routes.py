"""
Main configuration of API routes
"""

from fastapi import APIRouter

from app.api.endpoints import health, workspace, permit, workspace_history, test_integration, auth

api_router = APIRouter()

# Endpoint to check service status
api_router.include_router(health.router, prefix="/health", tags=["Health endpoint (health check)"])

# Auth endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication endpoint (pending to connect with Keycloak)"])

# Workspace endpoints
api_router.include_router(workspace.router, prefix="/workspaces", tags=["Workspaces endpoint"])

# Permit endpoints
api_router.include_router(permit.router, prefix="/permits", tags=["Permits endpoint"])

# Workspace History endpoints
api_router.include_router(workspace_history.router, prefix="/workspace-history", tags=["Workspace History endpoint"])

# Test Integration endpoints
api_router.include_router(test_integration.router, prefix="/test-integration", tags=["Test Integration endpoint (just for testing purposes)"])
