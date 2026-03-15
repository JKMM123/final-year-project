from src.areas.services.areasService import AreasService
from fastapi import Request



async def get_areas_service(request: Request) -> AreasService:
    return request.app.state.areas_service