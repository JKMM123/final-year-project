from fastapi import FastAPI, Request

from globals.responses.responses import (
    not_found_error_response,
    bad_request_error_response,
    forbidden_error_response,
)

from src.templates.exceptions.exceptions import (
    TemplateNotFoundError,
    TemplateAlreadyExistsError,
    InvalidAreasProvidedError,
    InvalidCustomersProvidedError,
    InvalidPackagesProvidedError,
)


def register_templates_exceptions(app: FastAPI):
    @app.exception_handler(TemplateNotFoundError)
    async def template_not_found_handler(request: Request, exc: TemplateNotFoundError):
        return not_found_error_response(message=exc.message)

    @app.exception_handler(TemplateAlreadyExistsError)
    async def template_already_exists_handler(request: Request, exc: TemplateAlreadyExistsError):
        return bad_request_error_response(message=exc.message)

    @app.exception_handler(InvalidAreasProvidedError)
    async def invalid_areas_provided_handler(request: Request, exc: InvalidAreasProvidedError):
        return bad_request_error_response(message=exc.message)

    @app.exception_handler(InvalidCustomersProvidedError)
    async def invalid_customers_provided_handler(request: Request, exc: InvalidCustomersProvidedError):
        return bad_request_error_response(message=exc.message)

    @app.exception_handler(InvalidPackagesProvidedError)
    async def invalid_packages_provided_handler(request: Request, exc: InvalidPackagesProvidedError):
        return bad_request_error_response(message=exc.message)
