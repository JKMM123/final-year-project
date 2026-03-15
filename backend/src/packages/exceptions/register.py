from fastapi import FastAPI, Request


from globals.responses.responses import (
    not_found_error_response,
    bad_request_error_response,
)

from src.packages.exceptions.exceptions import (
    PackagesNotFoundError,
    PackageAlreadyExistsError,
    PackageInUseError,
    InvalidPackageError
)


def register_packages_exceptions(app: FastAPI):
    @app.exception_handler(PackagesNotFoundError)
    async def packages_not_found_error_handler(request: Request, exc: PackagesNotFoundError):
        return not_found_error_response(
            message=exc.message
        )

    @app.exception_handler(PackageAlreadyExistsError)
    async def package_already_exists_error_handler(request: Request, exc: PackageAlreadyExistsError):
        return bad_request_error_response(
            message=exc.message,
        )
    
    @app.exception_handler(PackageInUseError)
    async def package_in_use_error_handler(request: Request, exc: PackageInUseError):
        return bad_request_error_response(
            message=exc.message,
        )
    
    @app.exception_handler(InvalidPackageError)
    async def invalid_package_error_handler(request: Request, exc: InvalidPackageError):
        return bad_request_error_response(
            message=exc.message,
        )
