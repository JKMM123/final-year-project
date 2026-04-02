from typing import Optional
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from db.postgres.dependancies import get_async_session

from src.templates.dependancies.templatesServiceDependancy import get_templates_service

from src.templates.services.templatesService import TemplatesService


templates_router = APIRouter(
    prefix="/api/v1/templates",
    tags=["templates"],
)

 
@templates_router.get("/search")
async def search_templates(
    request: Request,
    templates_service: TemplatesService = Depends(get_templates_service),
    session: AsyncSession = Depends(get_async_session),
):
    return await templates_service.search_templates(request, session)

@templates_router.post("/create")
async def create_template(
    request: Request,
    templates_service: TemplatesService = Depends(get_templates_service),
    session: AsyncSession = Depends(get_async_session),
):
    return await templates_service.create_template(request, session)


@templates_router.get("/{template_id}")
async def get_template(
    request: Request,
    templates_service: TemplatesService = Depends(get_templates_service),
    session: AsyncSession = Depends(get_async_session),
):
    return await templates_service.get_template(request, session)


@templates_router.delete("/{template_id}")
async def delete_template(
    request: Request,
    templates_service: TemplatesService = Depends(get_templates_service),
    session: AsyncSession = Depends(get_async_session),
):
    return await templates_service.delete_template(request, session)


@templates_router.put("/{template_id}")
async def update_template(
    request: Request,
    templates_service: TemplatesService = Depends(get_templates_service),
    session: AsyncSession = Depends(get_async_session),
):
    return await templates_service.update_template(request, session)         

