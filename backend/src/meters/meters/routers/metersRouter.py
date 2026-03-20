from typing import Optional
from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from db.postgres.dependancies import get_async_session

from src.meters.dependancies.metersServiceDependancy import get_meters_service
from src.meters.dependancies.meterFileServiceDependancy import get_meter_file_service
from src.meters.services.metersService import MetersService
from src.meters.services.meterFileService import MeterFileService

meters_router = APIRouter(
    prefix="/api/v1/meters",
    tags=["meters"],
)

 
@meters_router.post("/upload")
async def upload_meters(
    request: Request,
    meters_file: Optional[UploadFile] = File(None),
    session: AsyncSession = Depends(get_async_session),
    meter_file_service: MeterFileService = Depends(get_meter_file_service)
):
    return await meter_file_service.upload_meters(request, meters_file, session)


@meters_router.post("/create")
async def create_meter(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    meters_service: MetersService = Depends(get_meters_service)
):
    return await meters_service.create_meter(request, session)


@meters_router.post("/search")
async def search_meters(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    meters_service: MetersService = Depends(get_meters_service)
):
    return await meters_service.search_meters(request, session)


@meters_router.get("/qr-codes")
async def get_meter_qr_codes(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    meters_service: MetersService = Depends(get_meters_service)
):
    return await meters_service.get_meter_qr_codes(request, session)


@meters_router.delete("/delete")
async def delete_meters(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    meters_service: MetersService = Depends(get_meters_service)
):
    return await meters_service.delete_meters(request, session)


@meters_router.get("/{meter_id}")
async def get_meter(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    meters_service: MetersService = Depends(get_meters_service)
):
    return await meters_service.get_meter(request, session)


@meters_router.put("/{meter_id}")
async def update_meter(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    meters_service: MetersService = Depends(get_meters_service)
):
    return await meters_service.update_meter(request, session)


@meters_router.delete("/{meter_id}")
async def delete_meter(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    meters_service: MetersService = Depends(get_meters_service)
):
    return await meters_service.delete_meter(request, session)


@meters_router.get("/{meter_id}/qr-code")
async def get_meter_qr_code(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    meters_service: MetersService = Depends(get_meters_service)
):
    return await meters_service.get_meter_qr_code(request, session)


