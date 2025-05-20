"""
Endpoints to check the service status
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/", summary="Check API status")
async def health_check():
    """
    Check the status of the API.
    Returns a JSON response indicating the service is working correctly.
    """
    return {"status": "ok", "message": "The service is working correctly"}
