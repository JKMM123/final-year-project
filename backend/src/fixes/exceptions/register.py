from fastapi import FastAPI, Request
from globals.responses.responses import not_found_error_response, bad_request_error_response, validation_error_response, internal_server_error_response
from globals.exceptions.global_exceptions import InternalServerError, ValidationError
from src.fixes.exceptions.exceptions import (
    FixNotFoundError,
    MeterNotFoundError,
    MeterInactiveError,
)


def register_fixes_exceptions(app: FastAPI):
    """Register all exception handlers for the FastAPI app"""

    @app.exception_handler(FixNotFoundError)
    async def handle_fix_not_found_error(request: Request, exc: FixNotFoundError):
        return not_found_error_response(
            message=exc.message
        )

    @app.exception_handler(MeterNotFoundError)
    async def handle_meter_not_found_for_fix_error(request: Request, exc: MeterNotFoundError):
        return not_found_error_response(
            message=exc.message
        )
    
    @app.exception_handler(MeterInactiveError)
    async def handle_meter_inactive_error(request: Request, exc: MeterInactiveError):
        return bad_request_error_response(
            message=exc.message
        )

    