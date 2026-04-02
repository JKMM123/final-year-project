from fastapi import Request
from src.templates.services.templatesService import TemplatesService


async def get_templates_service(request: Request) -> TemplatesService:
    return request.app.state.templates_service

