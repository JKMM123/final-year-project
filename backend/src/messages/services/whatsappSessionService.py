from src.messages.queries.whatsAppSessionQueries import WhatsAppSessionQueries
from sqlalchemy import select
from globals.config.config import WA_SENDER_API_PAT, WA_WEBHOOK_URL
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request
from globals.utils.requestValidation import validate_request
from globals.utils.logger import logger
from globals.responses.responses import success_response
from globals.exceptions.global_exceptions import ValidationError, InternalServerError
from sqlalchemy.ext.asyncio import AsyncSession
from src.messages.schemas.createSessionSchema import CreateSessionRequestBody
from src.messages.exceptions.exceptions import (
    WhatsAppSessionNotFoundError
)
from wasenderapi.errors import WasenderAPIError


class WhatsAppSessionService:
    def __init__(self):
        self.queries = WhatsAppSessionQueries()


    async def create_session(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            body_model=CreateSessionRequestBody
        )
        if not valid:
            logger.error(f"Validation error in create_session: {validated_request}")
            raise ValidationError(validated_request)

        try:
            name = validated_request.get('body').get('name')
            phone_number = validated_request.get('body').get('phone_number')

            create_session_url = "https://www.wasenderapi.com/api/whatsapp-sessions"
            headers = {
                "Authorization": f"Bearer {WA_SENDER_API_PAT}",
                "Content-Type": "application/json"
            }
            data = {
                "name": f"{name}",
                "phone_number": f"+961{phone_number}",
                "account_protection": True,
                "log_messages": False,
                "read_incoming_messages": False,
                "webhook_url": WA_WEBHOOK_URL,
                "webhook_enabled": True,
                "webhook_events": [
                    "session.status"
                ]
            }

            async with httpx.AsyncClient() as client:
                # create session
                create_session_response = await client.post(create_session_url, headers=headers, json=data)
                create_session_response.raise_for_status()
                logger.info(f"WhatsApp session created successfully for {name}.")
                create_session_response_data = create_session_response.json()

                # get connection qrcode
                session_id = create_session_response_data.get('data').get('id')
                api_key = create_session_response_data.get('data').get('api_key')
                webhook_secret = create_session_response_data.get('data').get('webhook_secret')

                connect_session_url = f"https://www.wasenderapi.com/api/whatsapp-sessions/{session_id}/connect"
                connect_session_response = await client.post(connect_session_url, headers=headers)
                connect_session_response.raise_for_status()
                logger.info(f"WhatsApp session connection qr code generated successfully for {name}.")
                connect_session_response_data = connect_session_response.json()

                # Store session information in the database
                whatsapp_session = await self.queries.create_session(
                    session_id=session_id,
                    name=name,
                    api_key=api_key,
                    webhook_secret=webhook_secret,
                    phone_number=phone_number,
                    session=session
                )

            return success_response(
                message="Session created successfully.",
                data=connect_session_response_data
            )
        
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 422:
                logger.error(f"Validation error in create_session: {e.response.text}")
                raise ValidationError(
                    message="Phone number already has a session.",
                    errors=[]
                    )
            else:
                logger.error(f"Failed to create WhatsApp session: {e.response.text}")
                raise InternalServerError(f"Failed to create WhatsApp session: {e.response.text}")
            
        except Exception as e:
            logger.error(f"Error in create_session: {e}")
            raise InternalServerError("An error occurred while creating session.")


    async def get_session_status(self, request: Request, session: AsyncSession):
        try:
            # get api key
            whatsapp_session = await self.queries.get_session(session)
            api_key = whatsapp_session.api_key
            get_session_status_url = "https://www.wasenderapi.com/api/status"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(get_session_status_url, headers=headers)
                response.raise_for_status()
                response_data = response.json()

            return success_response(
                message="Session status retrieved successfully.",
                data=response_data
            )
        
        except WhatsAppSessionNotFoundError:
            raise

        except Exception as e:
            logger.error(f"Error in get_session_status: {e}")
            raise InternalServerError("An error occurred while retrieving session status.")


    async def connect_session(self, request: Request, session:AsyncSession):
        try:
            headers = {
                "Authorization": f"Bearer {WA_SENDER_API_PAT}",
                "Content-Type": "application/json"
            }
            session = await self.queries.get_session(session)
            session_id = session.session_id
            connect_session_url = f"https://www.wasenderapi.com/api/whatsapp-sessions/{session_id}/connect"
            async with httpx.AsyncClient() as client:
                # get connection qrcode
                connect_session_response = await client.post(connect_session_url, headers=headers)
                connect_session_response.raise_for_status()
                connect_session_response_data = connect_session_response.json()
                logger.info(f"WhatsApp session qrcode generated successfully.")

            return success_response(
                message="WhatsApp session connected successfully.",
                data=connect_session_response_data
            )
        

        except WhatsAppSessionNotFoundError as e:
            logger.error(f"WhatsApp session error: {e}")
            raise

        except Exception as e:
            logger.error(f"Error in connect_session: {e}")
            raise InternalServerError("An error occurred while connecting session.")


    async def delete_session(self, request: Request, session:AsyncSession):
        try:
            whatsapp_session = await self.queries.get_session(session)
            session_id = whatsapp_session.session_id

            headers = {
                "Authorization": f"Bearer {WA_SENDER_API_PAT}",
                "Content-Type": "application/json"
            }
            delete_session_url = f"https://www.wasenderapi.com/api/whatsapp-sessions/{session_id}"
            async with httpx.AsyncClient() as client:
                response = await client.delete(delete_session_url, headers=headers)
                response.raise_for_status()
                # response_data = response.json()
                logger.info(f"WhatsApp session disconnected successfully.")

                await self.queries.delete_session(session)

            return success_response(
                message="WhatsApp session disconnected successfully.",
                data=[]
            )

        except WhatsAppSessionNotFoundError:
            raise

        except Exception as e:
            logger.error(f"Error in delete_session: {e}")
            raise InternalServerError("An error occurred while deleting session.")
        

    async def check_session_exists_and_connected(self, session:AsyncSession):
        try:
            whatsapp_session = await self.queries.get_session(session)
            api_key = whatsapp_session.api_key
            get_session_status_url = "https://www.wasenderapi.com/api/status"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(get_session_status_url, headers=headers)
                response.raise_for_status()
                response_data = response.json()

                status = response_data.get('status')
                if status != "connected":
                   logger.error("WhatsApp session is not connected.")
                   raise ValidationError(
                       message="WhatsApp session is not connected. Please connect the session before sending messages.",
                       errors=[]
                   )

            return api_key
        
        except ValidationError:
            raise

        except WhatsAppSessionNotFoundError:
            logger.error("WhatsApp session not found.")
            raise ValidationError(
                message="WhatsApp session not found. Please create and connect a session before sending messages.",
                errors=[]
            )

        except Exception as e:
            logger.error(f"Error in check_session_exists_and_connected: {e}")
            raise InternalServerError("An error occurred while checking WhatsApp session.")


    

