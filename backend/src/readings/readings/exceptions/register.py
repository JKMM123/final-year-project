from fastapi import FastAPI, Request


from globals.responses.responses import (
    not_found_error_response,
    bad_request_error_response,
)

from src.readings.exceptions.exceptions import (
    ReadingNotFoundException,
    InvalidReadingValueException,
    ReadingAlreadyVerifiedException,
    ReadingFrequencyException,
    DuplicateReadingDateException,
    NoReadingsFoundForActiveMetersError,
    MissingReadingsForActiveMetersError,
    UnverifiedReadingsError,
    FixedMeterCannotHaveUsageReadingsError
)


def register_readings_exceptions(app: FastAPI):
    """
    Registers the readings exceptions with the FastAPI application.
    """
    @app.exception_handler(ReadingNotFoundException)
    async def reading_not_found_error_handler(request: Request, exc: ReadingNotFoundException):
        return not_found_error_response(
            message=exc.message
        )
    
    @app.exception_handler(InvalidReadingValueException)
    async def invalid_reading_value_error_handler(request: Request, exc: InvalidReadingValueException
):
        return bad_request_error_response(
            message=exc.message,
        )
    
    @app.exception_handler(ReadingAlreadyVerifiedException)
    async def reading_already_verified_error_handler(request: Request, exc: ReadingAlreadyVerifiedException
):
        return bad_request_error_response(
            message=exc.message,
        )
    
    @app.exception_handler(ReadingFrequencyException)
    async def reading_frequency_error_handler(request: Request, exc: ReadingFrequencyException):
        return bad_request_error_response(
            message=exc.message,
        )
    
    @app.exception_handler(DuplicateReadingDateException)
    async def duplicate_reading_date_error_handler(request: Request, exc: DuplicateReadingDateException):
        return bad_request_error_response(
            message=exc.message,
        )
    
    @app.exception_handler(NoReadingsFoundForActiveMetersError)
    async def no_readings_found_for_active_meters_error_handler(request: Request, exc: NoReadingsFoundForActiveMetersError):
        return not_found_error_response(
            message=exc.message
        )
    
    @app.exception_handler(MissingReadingsForActiveMetersError)
    async def missing_readings_for_active_meters_error_handler(request: Request, exc: MissingReadingsForActiveMetersError):
        return not_found_error_response(
            message=exc.message,
        )
    
    @app.exception_handler(UnverifiedReadingsError)
    async def unverified_readings_error_handler(request: Request, exc: UnverifiedReadingsError):
        return bad_request_error_response(
            message=exc.message,
        )
    
    @app.exception_handler(FixedMeterCannotHaveUsageReadingsError)
    async def fixed_meter_cannot_have_usage_readings_error_handler(request: Request, exc: FixedMeterCannotHaveUsageReadingsError):
        return bad_request_error_response(
            message=exc.message,
        )
    
