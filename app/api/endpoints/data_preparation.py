
from fastapi import APIRouter, HTTPException
from app.schemas.data_preparation import DataPreparationRequest
from app.services.data_preparation import DataPreparationService
import time
import asyncio

router = APIRouter()

service = DataPreparationService()


@router.get("/", summary="Check API status")
async def data_preparation_check():
    """
    Check the status of the API.
    Returns a JSON response indicating the service is working correctly.
    """

    # This study is part of collaboration 2, and consists of UPM and IKNL
    

    return {"status": "ok", "message": "Data preparation works: The service is working correctly"}

@router.post("/create_task")
async def run_data_preparation(data: DataPreparationRequest):
    try:
        task_result = service.create_v6_task(data)

        task_id = task_result.task_id
        responseStatus = service.run_v6_task(task_id)

        while responseStatus != "completed":
            await asyncio.sleep(3)   # No bloquea el servidor
            responseStatus = service.run_v6_task(task_id)

        return service.results_v6_task(task_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
