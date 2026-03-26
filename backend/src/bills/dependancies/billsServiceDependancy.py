from fastapi import Request
from src.bills.services.billsService import BillsService


async def get_bills_service(request: Request) -> BillsService:
    return request.app.state.bills_service
