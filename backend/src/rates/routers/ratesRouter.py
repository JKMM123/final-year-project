from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from db.postgres.dependancies import get_async_session

from src.rates.dependancies.ratesServiceDependancy import get_rates_service
from src.rates.services.ratesService import RatesService


rates_router = APIRouter(
    prefix="/api/v1/rates",
    tags=["rates"],
)


@rates_router.get("/search")
async def search_rates(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    rates_service: RatesService = Depends(get_rates_service),
):
    """
    Get all rates.
    """
    return await rates_service.search_rates(request, session)


@rates_router.post("/create")
async def create_rates(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    rates_service: RatesService = Depends(get_rates_service),
):
    """
    Create new rates.
    """
    return await rates_service.create_rates(request, session)


@rates_router.get("/all/{year}")
async def get_all_rates_by_year(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    rates_service: RatesService = Depends(get_rates_service),
):
    """
    Get all rates for a specific year.
    """
    return await rates_service.get_all_rates_by_year(request, session)


@rates_router.put("/{rate_id}")
async def update_rates(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    rates_service: RatesService = Depends(get_rates_service),
):
    """
    Update rates.
    """
    return await rates_service.update_rates(request, session)


@rates_router.delete("/{rate_id}")
async def delete_rates(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    rates_service: RatesService = Depends(get_rates_service),
):
    """
    Delete rates.
    """
    return await rates_service.delete_rates(request, session)


@rates_router.get("/{effective_date}")
async def get_rates_by_date(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    rates_service: RatesService = Depends(get_rates_service),
):
    """
    Get rates by date.
    """
    return await rates_service.get_rates_by_date(request, session)
