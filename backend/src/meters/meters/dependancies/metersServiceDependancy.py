from fastapi import Request
from src.meters.services.metersService import MetersService


async def get_meters_service(request: Request) -> MetersService:
    return request.app.state.meters_service
