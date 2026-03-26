from fastapi import FastAPI, Request


from globals.responses.responses import (
    not_found_error_response,
    bad_request_error_response,
)

from src.bills.exceptions.exceptions import (
        BillNotFoundError,
        BillAlreadyExistsError,
        BillsGenerationRestrictionError,
        DeletePaidBillError,
        MessagesSendingError
    )


def register_bills_exceptions(app: FastAPI):
    
    from globals.responses.responses import (
        not_found_error_response,
        bad_request_error_response
    )

    @app.exception_handler(BillNotFoundError)
    async def handle_bill_not_found(request: Request, exc: BillNotFoundError):
        return not_found_error_response(
            message=exc.message
        )
    
    
    @app.exception_handler(BillAlreadyExistsError)
    async def handle_bill_conflict(request: Request, exc: BillAlreadyExistsError):
        return bad_request_error_response(
            message=exc.message
        )
    
    @app.exception_handler(BillsGenerationRestrictionError)
    async def handle_bills_generation_restriction(request: Request, exc: BillsGenerationRestrictionError):
        return bad_request_error_response(
            message=exc.message
        )

    @app.exception_handler(DeletePaidBillError)
    async def handle_bill_already_paid(request: Request, exc: DeletePaidBillError):
        return bad_request_error_response(
            message=exc.message
        )

    @app.exception_handler(MessagesSendingError)
    async def handle_messages_sending_error(request: Request, exc: MessagesSendingError):
        return bad_request_error_response(
            message=exc.message
        )
