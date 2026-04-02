import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from src.templates.exceptions.exceptions import (
    TemplateNotFoundError,
    InvalidAreasProvidedError,
    InvalidCustomersProvidedError,
    InvalidPackagesProvidedError,
)
from fastapi import Request
from globals.utils.requestValidation import validate_request
from globals.utils.logger import logger
from globals.responses.responses import success_response
from globals.exceptions.global_exceptions import ValidationError, InternalServerError
from sqlalchemy.ext.asyncio import AsyncSession
from globals.config.config import BUCKET_NAME
from src.messages.queries.messagesQueries import MessagesQueries
from src.messages.schemas.sendMessagesSchema import sendMessagesRequestBody
from src.messages.schemas.createSessionSchema import CreateSessionRequestBody
from src.messages.services.whatsappSessionService import WhatsAppSessionService
from zoneinfo import ZoneInfo
from datetime import datetime, timezone
from src.messages.tasks.sendMessagesTask import send_messages_task
from wasenderapi import WasenderAsyncClient, create_async_wasender
from globals.config.config import WA_SENDER_API_PAT
from wasenderapi.errors import WasenderAPIError
from wasenderapi.models import TextOnlyMessage


class MessagesService:
    def __init__(self):
        self.messages_queries = MessagesQueries()
        self.whatsapp_session_service = WhatsAppSessionService()
        self.timezone = ZoneInfo("Asia/Beirut")
        self.wa_async_client = create_async_wasender(api_key=WA_SENDER_API_PAT)
        logger.info("Messages Service initialized successfully.")


    async def send_messages(self, request: Request, session: AsyncSession):
        try:

            check_session_exists_and_connected = await self.whatsapp_session_service.check_session_exists_and_connected(session)

            valid, validated_request = await validate_request(
                request=request,
                body_model=sendMessagesRequestBody
            )
            if not valid:
                logger.error(f"Invalid request: {validated_request}")
                raise ValidationError(validated_request)

            user_phone_number = request.state.user.get('phone_number')

            body = validated_request.get('body')
            customers_to_notify, template = await self.messages_queries.get_customers_to_notify(
                body,
                session
            )
            if not customers_to_notify:
                logger.warning("No customers to notify.")
                return success_response(
                    message="No customers to notify found based on the provided filters.",
                    data=[]
                )
            
            customers_to_notify_count = len(customers_to_notify)
            logger.info(f"Number of customers to notify: {customers_to_notify_count}")

            send_immediately = body.get("send_immediately", False)
            scheduled_at = body.get("scheduled_at", None)
            if send_immediately:
                # Send messages immediately
                task = send_messages_task.delay(customers_to_notify, template, user_phone_number)
                logger.info("Sending messages immediately.")

            else:
                # Schedule messages for later
                scheduled_at_beirut = datetime.fromisoformat(scheduled_at)
                scheduled_at_utc = scheduled_at_beirut.astimezone(timezone.utc)
                task = send_messages_task.apply_async(
                    args=[customers_to_notify, template, user_phone_number],
                    eta=scheduled_at_utc
                ) 
                logger.info(f"Scheduling messages to be sent at {scheduled_at_utc}.")

            return success_response(
                message="Messages sent successfully.",
                data={
                    "task_id": task.id,
                    "customers": len(customers_to_notify)
                }
            )

        except (
            TemplateNotFoundError,
            InvalidCustomersProvidedError,
            ValidationError,
            InvalidAreasProvidedError,
            InvalidPackagesProvidedError
        ):
            raise

        except Exception as e:
            logger.error(f"Error in send_messages: {e}")
            raise InternalServerError("An error occurred while sending messages.")


    async def send_message(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
        )
        if not valid:
            logger.error(f"Validation error in send_message: {validated_request}")
            raise ValidationError(validated_request)

        try:
            pass



        except Exception as e:
            logger.error(f"Error in send_message: {e}")
            raise InternalServerError("An error occurred while sending the message.")


