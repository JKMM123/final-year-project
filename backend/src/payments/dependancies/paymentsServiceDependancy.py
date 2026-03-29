from fastapi import Request
from src.payments.services.paymentsService import PaymentsService


async def get_payments_service(request: Request) -> PaymentsService:
    return request.app.state.payments_service
