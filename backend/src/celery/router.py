from fastapi import APIRouter, Request
from celery.result import AsyncResult
from src.celery.celery_app import celery_app
from globals.responses.responses import success_response, internal_server_error_response, validation_error_response
from globals.utils.logger import logger
from globals.utils.requestValidation import validate_request
from src.celery.schemas import CeleryTaskStatusRequestPath


celery_router = APIRouter(
    prefix="/api/v1/tasks",
    tags=["tasks"],
)


@celery_router.get("/{task_id}/status")
async def get_task_status(request: Request):
    try:
        valid, validated_request = await validate_request(
            request=request,
            path_model=CeleryTaskStatusRequestPath
        )
        if not valid:
            logger.error(f"Validation error in get_task_status: {validated_request}")
            return validation_error_response(errors=validated_request)

        task_id = str(validated_request.get('path').get('task_id'))
        task_result = AsyncResult(task_id, app=celery_app)

        logger.info(f"Fetched task status for {task_id}: {task_result.status}")
        return success_response(
            message="Task status fetched successfully",
            data = {
                "task_id": task_id,
                "status": task_result.status,   
                "result": task_result.result if task_result.successful() else None,
            }
        )
    except Exception as e:
        logger.error(f"Error fetching task status for {task_id}: {e}")
        return internal_server_error_response(message=str(e))

