from typing import Optional
from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from db.postgres.dependancies import get_async_session

from src.readings.dependancies.readingsServiceDependancy import get_readings_service
from src.readings.dependancies.scanningServiceDepandancy import get_scanning_service

from src.readings.services.readingsService import ReadingsService
from src.readings.services.scanningServiceV2 import ScanningService


readings_router = APIRouter(
    prefix="/api/v1/readings",
    tags=["readings"],
)

 
@readings_router.post("/create")
async def create_reading(
    request: Request,
    reading: Optional[UploadFile] = File(None),
    readings_service: ReadingsService = Depends(get_readings_service),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Create a new reading.
    """
    return await readings_service.create_reading(request, reading, session)


@readings_router.post("/search")
async def search_readings(
    request: Request,
    readings_service: ReadingsService = Depends(get_readings_service),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Search for readings based on query parameters.
    """
    return await readings_service.search_readings(request, session)


@readings_router.get("/summary")
async def get_readings_summary(
    request: Request,
    readings_service: ReadingsService = Depends(get_readings_service),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get all untaken readings.
    """
    return await readings_service.get_readings_summary(request, session)


@readings_router.post("/verify-all")
async def verify_all_readings(
    request: Request,
    readings_service: ReadingsService = Depends(get_readings_service),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Verify all readings.
    """
    return await readings_service.verify_all_readings(request, session)


@readings_router.get("/{reading_id}")
async def get_reading(
    request: Request,
    readings_service: ReadingsService = Depends(get_readings_service),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get a reading by its ID.
    """
    return await readings_service.get_reading(request,session)


@readings_router.put("/{reading_id}")
async def update_reading(
    request: Request,
    readings_service: ReadingsService = Depends(get_readings_service),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Update a reading by its ID.
    """
    return await readings_service.update_reading(request, session)


@readings_router.delete("/{reading_id}")
async def delete_reading(
    request: Request,
    readings_service: ReadingsService = Depends(get_readings_service),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Delete a reading by its ID.
    """
    return await readings_service.delete_reading(request,session)


@readings_router.post("/{meter_id}/scan")
async def scan_reading(
    request: Request,
    reading: Optional[UploadFile] = File(None),
    readings_service: ScanningService = Depends(get_scanning_service),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Scan a reading.
    """
    return await readings_service.scan_reading(request, session, reading)


