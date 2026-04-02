from wasenderapi import create_async_wasender, WasenderAsyncClient
from globals.config.config import WA_SENDER_API_PAT
from wasenderapi.errors import WasenderAPIError
from wasenderapi.models import TextOnlyMessage,  ImageUrlMessage
from globals.utils.logger import logger
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from db.postgres.connection import PostgresClient
from src.messages.queries.whatsAppSessionQueries import WhatsAppSessionQueries
from globals.responses.responses import success_response
from globals.exceptions.global_exceptions import ValidationError, InternalServerError
from fastapi import Request
from src.messages.queries.whatsAppSessionQueries import WhatsAppSessionQueries
from fastapi.responses import StreamingResponse
import asyncio
from typing import Dict, Any
import json
from globals.config.config import FRONT_END_URL


class WhatsappMessagesService:
    def __init__(self):
        self.api_key = None
        self.webhook_secret = None
        self._initialized = False
        self.whatsapp_session_queries = WhatsAppSessionQueries()
        self.event_queues: Dict[str, asyncio.Queue] = {}  
        self._queue_lock = asyncio.Lock()
        logger.info("Whatsapp Messages Service initialized successfully.")


    async def _ensure_initialized(self):
        """Initialize the client on first use"""
        if not self._initialized:
            api_key, webhook_secret = self.get_secrets()
            self.api_key = api_key
            self.webhook_secret = webhook_secret
            logger.info("Wasender Async Client initialized successfully.")
            self._initialized = True


    async def create_async_client(self):
        """Create an asynchronous client instance"""
        if not self._initialized:
            await self._ensure_initialized()

        wa_async_client = create_async_wasender(
                personal_access_token=WA_SENDER_API_PAT,
                api_key=self.api_key,
                webhook_secret=self.webhook_secret
            )
        return wa_async_client
        

    def get_secrets(self):
        try:
            whatsapp_session_queries = WhatsAppSessionQueries()
            with PostgresClient.get_sync_session() as session:
                session_data = whatsapp_session_queries.get_session_sync(session=session)
            return session_data.api_key, session_data.webhook_secret    
        
        except Exception as e:
            logger.error(f"An error occurred while retrieving API key: {str(e)}")
            raise


    async def send_whatsapp_message(self, phone_number: str, message: str, image_url: str = None):
        try:
            wa_async_client = await self.create_async_client()
            async with wa_async_client as client:
                if image_url:
                    text_payload = ImageUrlMessage(
                                        to=f"+961{phone_number}",
                                        text=message,
                                        imageUrl=image_url
                                )
                else:
                    text_payload = TextOnlyMessage(
                                        to=f"+961{phone_number}",
                                        text=message
                                        )
                
                logger.info(f"WhatsApp message sent successfully to {phone_number}.")
                response = await client.send(text_payload)
                return response

        except WasenderAPIError as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            raise

        except Exception as e:
            logger.error(f"An error occurred while sending WhatsApp message: {str(e)}")
            raise


    async def handle_webhook_events(self, request: Request, session: AsyncSession):
        webhook_sig = request.headers.get("x-webhook-signature")
        if not webhook_sig:
            logger.error("Missing webhook signature.")
            raise ValidationError(errors="Missing webhook signature.")

        whatsapp_session = await self.whatsapp_session_queries.get_session(session=session)
        sig = whatsapp_session.webhook_secret 

        if webhook_sig != sig:
            logger.error("Invalid webhook signature.")
            raise ValidationError(errors="Invalid webhook signature.")
        
        try:
            body = await request.json()
            event = body.get('event', None)

            if not event:
                logger.warning("Webhook received without event type")
                return {"status": "ignored", "reason": "no event type"}

            if event == "session.status":
                status = body.get('data').get('status')
                event_data = {
                    "event": event,
                    "status": status
                }
                await self._broadcast_to_all_clients(event_data)
                logger.info(f"Session status event broadcasted: {status}")

            else:
                logger.warning(f"Unhandled webhook event type: {event}")
                pass

            return {
                "status": "received", 
                "event": event
                }


        except Exception as e:
            logger.error(f"Error in handle_webhook_events: {e}")
            raise InternalServerError("Error in handling webhook events")
        

    async def _broadcast_to_all_clients(self, event_data: Dict[str, Any]):
        """Broadcast event to all connected SSE clients"""
        async with self._queue_lock:
            if not self.event_queues:
                logger.debug("No connected clients to broadcast to")
                return
                
            # Send to all client queues
            disconnected_clients = []
            for client_id, queue in self.event_queues.items():
                try:
                    # Use put_nowait to avoid blocking if queue is full
                    queue.put_nowait(event_data)
                except asyncio.QueueFull:
                    logger.warning(f"Queue full for client {client_id}, marking for removal")
                    disconnected_clients.append(client_id)
                except Exception as e:
                    logger.error(f"Error broadcasting to client {client_id}: {e}")
                    disconnected_clients.append(client_id)
            
            # Clean up disconnected clients
            for client_id in disconnected_clients:
                self.event_queues.pop(client_id, None)
                logger.info(f"Removed disconnected client {client_id}")


    async def get_webhook_events(self, request: Request):
        """Server-Sent Events endpoint for real-time webhook events"""
        try:
            # Generate unique client ID
            client_id = f"client_{id(request)}"
            
            async def event_generator():
                # Create queue for this client
                client_queue = asyncio.Queue(maxsize=100)  # Limit queue size
                
                async with self._queue_lock:
                    self.event_queues[client_id] = client_queue
                
                logger.info(f"Client {client_id} connected to webhook events")
                
                try:
                    while True:
                        # Check if client disconnected
                        if await request.is_disconnected():
                            logger.info(f"Client {client_id} disconnected")
                            break
                        
                        try:
                            # Wait for new events with timeout
                            event_data = await asyncio.wait_for(
                                client_queue.get(), 
                                timeout=30.0  # Send heartbeat every 30 seconds
                            )
                            
                            # Format as SSE
                            sse_data = f"data: {json.dumps(event_data)}\n\n"
                            yield sse_data.encode()
                            
                        except asyncio.TimeoutError:
                            # Send heartbeat to keep connection alive
                            heartbeat = f"data: {json.dumps({'event': 'heartbeat', 'timestamp': asyncio.get_event_loop().time()})}\n\n"
                            yield heartbeat.encode()
                            
                except Exception as e:
                    logger.error(f"Error in event generator for client {client_id}: {e}")
                    
                finally:
                    # Clean up client queue
                    async with self._queue_lock:
                        self.event_queues.pop(client_id, None)
                    logger.info(f"Cleaned up client {client_id}")

            return StreamingResponse(
                event_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": FRONT_END_URL,
                    "Access-Control-Allow-Headers": "Cache-Control",
                    "Access-Control-Allow-Credentials": "true",
                }
            )

        except Exception as e:
            logger.error(f"Error in get_webhook_events: {e}")
            raise InternalServerError("Error in getting webhook events")


    async def cleanup_disconnected_clients(self):
        """Periodic cleanup task for disconnected clients"""
        while True:
            try:
                await asyncio.sleep(300)  # Clean up every 5 minutes
                async with self._queue_lock:
                    if self.event_queues:
                        logger.info(f"Active webhook event clients: {len(self.event_queues)}")
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
