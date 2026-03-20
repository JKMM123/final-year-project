from fastapi import Request
from src.readings.services.readingsService import ReadingsService



async def get_readings_service(request: Request) -> ReadingsService:
    return request.app.state.readings_service
