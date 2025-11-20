
from fastapi import APIRouter

router = APIRouter()


@router.get("/", summary="Check API status")
async def data_preparation_check():
    """
    Check the status of the API.
    Returns a JSON response indicating the service is working correctly.
    """

    # This study is part of collaboration 2, and consists of UPM and IKNL
    

    return {"status": "ok", "message": "Data preparation works: The service is working correctly"}
