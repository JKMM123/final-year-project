from fastapi import APIRouter
from src.app_state.init import AppInitializer
from globals.responses.responses import success_response, internal_server_error_response

health_router = APIRouter()

@health_router.get("/health")
async def health_check():
    if AppInitializer.is_healthy():
        return success_response(
            message="Health check successful",
            data={"status": "healthy", "services": AppInitializer.get_status()}
        )
    else:
        return internal_server_error_response(
            message="Health check failed",
            fieldErrors={"status": "unhealthy", "services": AppInitializer.get_status()}
            )
    