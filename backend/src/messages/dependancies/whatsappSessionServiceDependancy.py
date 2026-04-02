from src.messages.services.whatsappSessionService import WhatsAppSessionService
from fastapi import Request



async def get_whatsapp_session_service(request: Request) -> WhatsAppSessionService:
    return request.app.state.whatsapp_session_service