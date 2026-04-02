from typing import Optional
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from db.postgres.dependancies import get_async_session
from src.messages.dependancies.messagesServiceDependancy import get_messages_service

from src.messages.services.whatsappSessionService import WhatsAppSessionService
from src.messages.dependancies.whatsappSessionServiceDependancy import get_whatsapp_session_service

from src.messages.services.whatsappMessagesService import WhatsappMessagesService
from src.messages.dependancies.whatsappMessagesServiceDependancy import get_whatsapp_messages_service

whatsapp_session_router = APIRouter(
    prefix="/api/v1/session",
    tags=["session"],
)




@whatsapp_session_router.post("/create")
async def create_session(
    request: Request,
    whatsapp_session_service: WhatsAppSessionService = Depends(get_whatsapp_session_service),
    session: AsyncSession = Depends(get_async_session)
):
    return await whatsapp_session_service.create_session(request, session)


@whatsapp_session_router.get("/status")
async def get_session_status(
    request: Request,
    whatsapp_session_service: WhatsAppSessionService = Depends(get_whatsapp_session_service),
    session: AsyncSession = Depends(get_async_session)
):
    return await whatsapp_session_service.get_session_status(request, session)


@whatsapp_session_router.get("/connect")
async def connect_session(
    request: Request,
    whatsapp_session_service: WhatsAppSessionService = Depends(get_whatsapp_session_service),
    session: AsyncSession = Depends(get_async_session)
):
    return await whatsapp_session_service.connect_session(request, session)



@whatsapp_session_router.delete("/delete")
async def delete_session(
    request: Request,
    whatsapp_session_service: WhatsAppSessionService = Depends(get_whatsapp_session_service),
    session: AsyncSession = Depends(get_async_session)
):
    return await whatsapp_session_service.delete_session(request, session)


@whatsapp_session_router.post("/webhook")
async def handle_webhook_events(
    request: Request,
    whatsapp_session_service: WhatsappMessagesService = Depends(get_whatsapp_messages_service),
    session: AsyncSession = Depends(get_async_session)
):
    return await whatsapp_session_service.handle_webhook_events(request, session)


@whatsapp_session_router.get("/webhook/events")
async def get_webhook_events(
    request: Request,
    whatsapp_session_service: WhatsappMessagesService = Depends(get_whatsapp_messages_service)
):
    return await whatsapp_session_service.get_webhook_events(request)
