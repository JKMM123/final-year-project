from src.messages.services.whatsappMessagesService import WhatsappMessagesService
from fastapi import Request



async def get_whatsapp_messages_service(request: Request) -> WhatsappMessagesService:
    return request.app.state.whatsapp_messages_service