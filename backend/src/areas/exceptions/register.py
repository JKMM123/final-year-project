from fastapi import FastAPI
from globals.responses.responses import not_found_error_response, bad_request_error_response, validation_error_response, internal_server_error_response
from src.areas.exceptions.exceptions import (
    AreaAlreadyExistsException,
    AreaNotFoundException,
    AreaLinkedToMetersException,
    InvalidAreaNameException
)


def register_areas_exceptions(app: FastAPI):
    """Register all exception handlers for the FastAPI app"""

    @app.exception_handler(AreaAlreadyExistsException)
    async def area_already_exists_exception_handler(request, exc: AreaAlreadyExistsException):
        return bad_request_error_response(
            message=exc.message,
        )
    
    @app.exception_handler(AreaNotFoundException)
    async def area_not_found_exception_handler(request, exc: AreaNotFoundException):
        return not_found_error_response(
            message=exc.message,
        )
    
    @app.exception_handler(AreaLinkedToMetersException)
    async def area_linked_to_customers_exception_handler(request, exc: AreaLinkedToMetersException):
        return bad_request_error_response(
            message=exc.message,
        )
    
    @app.exception_handler(InvalidAreaNameException)
    async def invalid_area_name_exception_handler(request, exc: InvalidAreaNameException):
        return bad_request_error_response(
            message=exc.message,
        )