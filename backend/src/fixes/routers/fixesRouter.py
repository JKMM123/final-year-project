from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from db.postgres.dependancies import get_async_session
from src.fixes.dependancies.fixesServiceDependancy import get_fixes_service
from src.fixes.services.fixesService import FixesService

fixes_router = APIRouter(
    prefix="/api/v1/fixes",
    tags=["fixes"],
)


@fixes_router.post("/create")
async def create_fix(
    request: Request,
    fixes_service: FixesService = Depends(get_fixes_service),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Create a new fix.
    """
    return await fixes_service.create_fix(request, session)


@fixes_router.delete("/delete")
async def delete_fixes(
    request: Request,
    fixes_service: FixesService = Depends(get_fixes_service),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Delete fixes by IDs.
    """
    return await fixes_service.delete_fixes(request, session)


@fixes_router.post("/search")
async def search_fixes(
    request: Request,
    fixes_service: FixesService = Depends(get_fixes_service),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Search for fixes.
    """
    return await fixes_service.search_fixes(request, session)


@fixes_router.get("/{fix_id}")
async def get_fix(
    request: Request,
    fixes_service: FixesService = Depends(get_fixes_service),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get a fix by ID.
    """
    return await fixes_service.get_fix(request, session)


@fixes_router.put("/{fix_id}")
async def update_fix(
    request: Request,
    fixes_service: FixesService = Depends(get_fixes_service),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Update a fix by ID.
    """
    return await fixes_service.update_fix(request, session)


