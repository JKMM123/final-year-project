from fastapi import FastAPI, Request
from globals.exceptions.global_exceptions import (
    InternalServerError,
    TimeOutException,
    BadRequestError,
    ValidationError,
    UnauthorizedError,
    ForbiddenError,
    TooManyRequestsError,
)

from globals.responses.responses import (
    internal_server_error_response,
    bad_request_error_response,
    validation_error_response,
    time_out_error_response,
    unauthorized_error_response,
    forbidden_error_response,
    too_many_requests_error_response,
)


def register_global_exceptions(app: FastAPI):

    @app.exception_handler(InternalServerError)
    async def error_logging_in_exception_handler(
        request: Request, exc: InternalServerError
    ):
        return internal_server_error_response(
            message=exc.message,
        )

    @app.exception_handler(ValidationError)
    async def validation_error_exception_handler(
        request: Request, exc: ValidationError
    ):
        return validation_error_response(message=exc.message, errors=exc.errors)

    @app.exception_handler(BadRequestError)
    async def bad_request_error_exception_handler(
        request: Request, exc: BadRequestError
    ):
        return bad_request_error_response(
            error=exc.error,
        )

    @app.exception_handler(TimeOutException)
    async def time_out_exception_handler(request: Request, exc: TimeOutException):
        return time_out_error_response(message=exc.message)

    @app.exception_handler(UnauthorizedError)
    async def unauthorized_error_exception_handler(
        request: Request, exc: UnauthorizedError
    ):
        return unauthorized_error_response(message=exc.message)

    @app.exception_handler(ForbiddenError)
    async def forbidden_error_exception_handler(request: Request, exc: ForbiddenError):
        return forbidden_error_response(message=exc.message)

    @app.exception_handler(TooManyRequestsError)
    async def too_many_requests_error_exception_handler(
        request: Request, exc: TooManyRequestsError
    ):
        return too_many_requests_error_response(message=exc.message)
