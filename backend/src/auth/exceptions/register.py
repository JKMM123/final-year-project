from fastapi import FastAPI, Request


from globals.responses.responses import (
    not_found_error_response,
    bad_request_error_response,
)

from src.auth.exceptions.exceptions import (
    UsernameOrPhoneNotFoundError,
    InvalidPasswordError,
    OTPAlreadyExistsError,
    OTPInvalidError,
    InvalidResetTokenError,
    ErrorSendingOTP

)



def register_auth_exceptions(app: FastAPI):
    
    @app.exception_handler(UsernameOrPhoneNotFoundError)
    async def username_or_phone_not_found_error_handler(request: Request, exc: UsernameOrPhoneNotFoundError):
        return not_found_error_response(
            message=exc.message
        )

    @app.exception_handler(InvalidPasswordError)
    async def invalid_password_error_handler(request: Request, exc: InvalidPasswordError):
        return bad_request_error_response(
            message=exc.message
        )

    @app.exception_handler(OTPAlreadyExistsError)
    async def otp_already_exists_error_handler(request: Request, exc: OTPAlreadyExistsError):
        return bad_request_error_response(
            message=exc.message
        )
    
    @app.exception_handler(OTPInvalidError)
    async def otp_invalid_error_handler(request: Request, exc: OTPInvalidError):
        return bad_request_error_response(
            message=exc.message
        )
    
    @app.exception_handler(InvalidResetTokenError)
    async def generic_exception_handler(request: Request, exc: InvalidResetTokenError):
        return bad_request_error_response(
            message=exc.message
        )
    
    @app.exception_handler(ErrorSendingOTP)
    async def error_sending_otp_handler(request: Request, exc: ErrorSendingOTP):
        return bad_request_error_response(
            message=exc.message
        )

    
