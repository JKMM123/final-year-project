from fastapi import FastAPI, Request

from globals.responses.responses import (
    not_found_error_response,
    bad_request_error_response,
    forbidden_error_response,
)

from src.payments.exceptions.exceptions import (
    PaymentNotFoundError,
    BillNotFoundError,
    MeterNotFoundError,
    BillAlreadyPaidError,
    InvalidPaymentAmountError,
    PaymentExceedsBillAmountError,
    InsufficientPermissionsError,
)


def register_payments_exceptions(app: FastAPI):
    @app.exception_handler(PaymentNotFoundError)
    async def payment_not_found_handler(request: Request, exc: PaymentNotFoundError):
        return not_found_error_response(message=exc.message)

    @app.exception_handler(BillNotFoundError)
    async def bill_not_found_handler(request: Request, exc: BillNotFoundError):
        return not_found_error_response(message=exc.message)

    @app.exception_handler(MeterNotFoundError)
    async def meter_not_found_handler(request: Request, exc: MeterNotFoundError):
        return not_found_error_response(message=exc.message)

    @app.exception_handler(BillAlreadyPaidError)
    async def bill_already_paid_handler(request: Request, exc: BillAlreadyPaidError):
        return bad_request_error_response(message=exc.message)

    @app.exception_handler(InvalidPaymentAmountError)
    async def invalid_payment_amount_handler(request: Request, exc: InvalidPaymentAmountError):
        return bad_request_error_response(message=exc.message)

    @app.exception_handler(PaymentExceedsBillAmountError)
    async def payment_exceeds_bill_amount_handler(request: Request, exc: PaymentExceedsBillAmountError):
        return bad_request_error_response(message=exc.message)

    @app.exception_handler(InsufficientPermissionsError)
    async def insufficient_permissions_handler(request: Request, exc: InsufficientPermissionsError):
        return forbidden_error_response(message=exc.message)