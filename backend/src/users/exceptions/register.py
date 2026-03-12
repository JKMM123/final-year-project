from fastapi import FastAPI, Request


from globals.responses.responses import (
    not_found_error_response,
    bad_request_error_response,
)

from src.users.exceptions.exceptions import (
    UserNotFoundError,
    UsernameAlreadyExistsError,
    PhoneNumberAlreadyExistsError,
    InsufficientPermissionsException
)



def register_users_exceptions(app: FastAPI):
    @app.exception_handler(UserNotFoundError)
    async def user_not_found_error_handler(request: Request, exc: UserNotFoundError):
        return not_found_error_response(message=exc.message)

    @app.exception_handler(UsernameAlreadyExistsError)
    async def username_already_exists_error_handler(request: Request, exc: UsernameAlreadyExistsError):
        return bad_request_error_response(message=exc.message)

    @app.exception_handler(PhoneNumberAlreadyExistsError)
    async def phone_number_already_exists_error_handler(request: Request, exc: PhoneNumberAlreadyExistsError):
        return bad_request_error_response(message=exc.message)
    
    @app.exception_handler(InsufficientPermissionsException)
    async def insufficient_permissions_error_handler(request: Request, exc: InsufficientPermissionsException):
        return bad_request_error_response(message=exc.message)