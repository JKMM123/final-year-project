from fastapi import FastAPI, Request


from globals.responses.responses import (
    not_found_error_response,
    bad_request_error_response,
)

from src.rates.exceptions.exec import (
    RatesException,
    
)


def register_rates_exceptions(app: FastAPI):
    @app.exception_handler(RatesException)
    async def rates_exception_handler(request: Request, exc: RatesException):
        return bad_request_error_response(
            message=exc.message
        )