from fastapi import Request
from src.meters.services.meterFileService import MeterFileService

async def get_meter_file_service(request: Request) -> MeterFileService:
    return request.app.state.meter_file_service
