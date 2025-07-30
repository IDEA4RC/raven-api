"""
Main configuration of API routes
"""

from fastapi import APIRouter

from app.api.endpoints import health, workspace, permit, workspace_history, auth, cohort, analysis, cohort_result

api_router = APIRouter()

# Endpoint to check service status
api_router.include_router(health.router, prefix="/health", tags=["Health endpoint (health check)"])

# Auth endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication endpoint"])

# Workspace endpoints
api_router.include_router(workspace.router, prefix="/workspaces", tags=["Workspaces endpoint"])

# Permit endpoints
api_router.include_router(permit.router, prefix="/permits", tags=["Permits endpoint"])

# Cohort endpoints
api_router.include_router(cohort.router, prefix="/cohorts", tags=["Cohorts endpoint"])

# Cohort Result endpoints
api_router.include_router(cohort_result.router, prefix="/cohort-results", tags=["Cohort Results endpoint"])

# Analysis endpoints
api_router.include_router(analysis.router, prefix="/analyses", tags=["Analyses endpoint"])

# Workspace History endpoints
api_router.include_router(workspace_history.router, prefix="/workspace-history", tags=["Workspace History endpoint"])