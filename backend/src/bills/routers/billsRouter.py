from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from db.postgres.dependancies import get_async_session

from src.bills.dependancies.billsServiceDependancy import get_bills_service
from src.bills.services.billsService import BillsService


bills_router = APIRouter(
    prefix="/api/v1/bills",
    tags=["bills"],
)


@bills_router.post("/generate")
async def generate_bills(
    request: Request,
    bills_service: BillsService = Depends(get_bills_service),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Endpoint to generate bills.
    """
    return await bills_service.generate_bills(request, session)


@bills_router.post("/search")
async def search_bills(
    request: Request,
    bills_service: BillsService = Depends(get_bills_service),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Endpoint to search bills.
    """
    return await bills_service.search_bills(request, session)


@bills_router.post("/download")
async def download_bills(
    request: Request,
    bills_service: BillsService = Depends(get_bills_service),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Endpoint to download a bill by ID.
    """
    return await bills_service.download_bills(request, session)

@bills_router.get("/statement")
async def get_statement(
    request: Request,
    bills_service: BillsService = Depends(get_bills_service),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Endpoint to get a statement of bills.
    """
    return await bills_service.get_statement(request, session)


@bills_router.get("/{bill_id}")
async def get_bill(
    request: Request,
    bills_service: BillsService = Depends(get_bills_service),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Endpoint to get a bill by ID.
    """
    return await bills_service.get_bill(request, session)


# @bills_router.put("/{bill_id}")
# async def update_bill(
#     request: Request,
#     bills_service: BillsService = Depends(get_bills_service),
#     session: AsyncSession = Depends(get_async_session)
# ):
#     """
#     Endpoint to update a bill by ID.
#     """
#     return await bills_service.update_bill(request, session)


@bills_router.delete("/{bill_id}")
async def delete_bill(
    request: Request,
    bills_service: BillsService = Depends(get_bills_service),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Endpoint to delete a bill by ID.
    """
    return await bills_service.delete_bill(request, session)


