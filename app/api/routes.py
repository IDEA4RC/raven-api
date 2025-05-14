"""
Main configuration of API routes
"""

from fastapi import APIRouter

from app.api.endpoints import health, workspace, permit, workspace_history, test_integration, auth

api_router = APIRouter()

# Endpoint to check service status
api_router.include_router(health.router, prefix="/health", tags=["health"])

# Auth endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Workspace endpoints
api_router.include_router(workspace.router, prefix="/workspaces", tags=["workspaces"])

# Permit endpoints
api_router.include_router(permit.router, prefix="/permits", tags=["permits"])

# Workspace History endpoints
api_router.include_router(workspace_history.router, prefix="/workspace-history", tags=["workspace-history"])

# Test Integration endpoints
api_router.include_router(test_integration.router, prefix="/test-integration", tags=["test-integration"])
