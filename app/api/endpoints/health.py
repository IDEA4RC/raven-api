"""
Endpoints to check the service status
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/", summary="Check API status")
async def health_check():
    return {"status": "ok", "message": "The service is working correctly"}
