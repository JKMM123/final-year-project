from fastapi import Request
from src.readings.services.scanningServiceV2 import ScanningService


async def get_scanning_service(request: Request) -> ScanningService:
    return request.app.state.scanning_service
