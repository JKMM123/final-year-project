from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from db.postgres.dependancies import get_async_session

from src.packages.dependancies.packagesServiceDependancy import get_packages_service
from src.packages.services.packagesService import PackagesService


packages_router = APIRouter(
    prefix="/api/v1/packages",
    tags=["packages"],
)


@packages_router.post("/create")
async def create_package(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    packages_service: PackagesService = Depends(get_packages_service),
):
    """
    Create a new package.
    """
    return await packages_service.create_package(request, session)


@packages_router.get("/search")
async def search_packages(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    packages_service: PackagesService = Depends(get_packages_service),
):
    """
    Search for packages.
    """
    return await packages_service.search_packages(request, session)


@packages_router.get("/{package_id}")
async def get_package(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    packages_service: PackagesService = Depends(get_packages_service),
):
    """
    Get package by amperage.
    """
    return await packages_service.get_package(request, session)


@packages_router.put("/{package_id}")
async def update_package(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    packages_service: PackagesService = Depends(get_packages_service),
):
    """
    Update a package by amperage.
    """
    return await packages_service.update_package(request, session)


@packages_router.delete("/{package_id}")
async def delete_package(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    packages_service: PackagesService = Depends(get_packages_service),
):
    """
    Delete a package by package_id.
    """
    return await packages_service.delete_package(request, session)



