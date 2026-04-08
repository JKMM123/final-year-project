from fastapi import Request
from src.fixes.services.fixesService import FixesService


async def get_fixes_service(request: Request) -> FixesService:
    return request.app.state.fixes_service
