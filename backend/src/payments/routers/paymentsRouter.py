from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from db.postgres.dependancies import get_async_session

from src.payments.dependancies.paymentsServiceDependancy import get_payments_service
from src.payments.services.paymentsService import PaymentsService
from db.postgres.dependancies import get_async_session



payments_router = APIRouter(
    prefix="/api/v1/payments",
    tags=["payments"],
)

@payments_router.post('/mark-as-paid')
async def mark_all_bills_as_paid(
    request: Request,
    payments_service: PaymentsService = Depends(get_payments_service),
    session: AsyncSession = Depends(get_async_session)
):
    return await payments_service.mark_all_bills_as_paid(request, session)


@payments_router.post('/create')
async def create_payment(
    request: Request,
    payments_service: PaymentsService = Depends(get_payments_service),
    session: AsyncSession = Depends(get_async_session)
):
    return await payments_service.create_payment(request, session)


@payments_router.get('/all')
async def get_all_payments_by_bill_id(
    request: Request,
    payments_service: PaymentsService = Depends(get_payments_service),
    session: AsyncSession = Depends(get_async_session)
):
    return await payments_service.get_all_payments_by_bill_id(request, session)


@payments_router.get('/{payment_id}')
async def get_payment_by_id(
    request: Request,
    payments_service: PaymentsService = Depends(get_payments_service),
    session: AsyncSession = Depends(get_async_session)
):
    return await payments_service.get_payment_by_id(request, session)


@payments_router.delete('/{payment_id}')
async def delete_payment(
    request: Request,
    payments_service: PaymentsService = Depends(get_payments_service),
    session: AsyncSession = Depends(get_async_session)
):
    return await payments_service.delete_payment(request, session)


@payments_router.put('/{payment_id}')
async def update_payment(
    request: Request,
    payments_service: PaymentsService = Depends(get_payments_service),
    session: AsyncSession = Depends(get_async_session)
):
    return await payments_service.update_payment(request, session)



