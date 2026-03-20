from fastapi import FastAPI, Request


from globals.responses.responses import (
    not_found_error_response,
    bad_request_error_response,
)

from src.meters.exceptions.exceptions import (
    MeterNotFoundError,
    CustomerNameAlreadyExistsError,
    CustomerPhoneNumberAlreadyExistsError,
    CustomerIdentityAddressAlreadyExistsError,
    MeterInactiveError,
    MeterInUseError,
    NoActiveMetersError,
    InvalidColumnsException,
    EmptyFileException,
    FileProcessingTimeoutException,
    InitialReadingRequiredError
)


def register_meters_exceptions(app: FastAPI):
    @app.exception_handler(MeterNotFoundError)
    async def meter_not_found_exception_handler(request: Request, exc: MeterNotFoundError):
        return not_found_error_response(
            message=exc.message
        )

    @app.exception_handler(CustomerNameAlreadyExistsError)
    async def customer_name_already_exists_exception_handler(request: Request, exc: CustomerNameAlreadyExistsError):
        return bad_request_error_response(
            message=exc.message
        )

    @app.exception_handler(CustomerPhoneNumberAlreadyExistsError)
    async def customer_phone_number_already_exists_exception_handler(request: Request, exc: CustomerPhoneNumberAlreadyExistsError):
        return bad_request_error_response(
            message=exc.message
        )
    
    @app.exception_handler(CustomerIdentityAddressAlreadyExistsError)
    async def customer_identity_address_already_exists_exception_handler(request: Request, exc: CustomerIdentityAddressAlreadyExistsError):
        return bad_request_error_response(
            message=exc.message
        )
    
    @app.exception_handler(MeterInactiveError)
    async def meter_inactive_exception_handler(request: Request, exc: MeterInactiveError):
        return bad_request_error_response(
            message=exc.message
        )
    
    @app.exception_handler(MeterInUseError)
    async def meter_in_use_exception_handler(request: Request, exc: MeterInUseError):
        return bad_request_error_response(
            message=exc.message
        )
    
    @app.exception_handler(NoActiveMetersError)
    async def no_active_meters_exception_handler(request: Request, exc: NoActiveMetersError):
        return not_found_error_response(
            message=exc.message
        )
    
    @app.exception_handler(InvalidColumnsException)
    async def invalid_columns_exception_handler(request: Request, exc: InvalidColumnsException):
        return bad_request_error_response(
            message=exc.message,
        )
    
    @app.exception_handler(EmptyFileException)
    async def empty_file_exception_handler(request: Request, exc: EmptyFileException):
        return bad_request_error_response(
            message=exc.message
        )
    
    @app.exception_handler(FileProcessingTimeoutException)
    async def file_processing_timeout_exception_handler(request: Request, exc: FileProcessingTimeoutException):
        return bad_request_error_response(
            message=exc.message
        )


    @app.exception_handler(InitialReadingRequiredError)
    async def initial_reading_required_exception_handler(request: Request, exc: InitialReadingRequiredError):
        return bad_request_error_response(
            message=exc.message
        )