from fastapi import FastAPI, Request


from globals.responses.responses import (
    not_found_error_response,
    bad_request_error_response,
)

from src.messages.exceptions.exceptions import (
    WhatsAppSessionNotFoundError,
    WhatsAppSessionAlreadyExistsError
)


def register_messages_exceptions(app: FastAPI):

    @app.exception_handler(WhatsAppSessionNotFoundError)
    async def handle_whatsapp_session_not_found_error(
        request: Request, exc: WhatsAppSessionNotFoundError
    ):
        return not_found_error_response(
            message=exc.message
        )

    @app.exception_handler(WhatsAppSessionAlreadyExistsError)
    async def handle_whatsapp_session_already_exists_error(
        request: Request, exc: WhatsAppSessionAlreadyExistsError
    ):
        return bad_request_error_response(
            message=exc.message
        )