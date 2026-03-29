from fastapi import Request
from src.rates.services.ratesService import RatesService



async def get_rates_service(request: Request) -> RatesService:
    return request.app.state.rates_service
