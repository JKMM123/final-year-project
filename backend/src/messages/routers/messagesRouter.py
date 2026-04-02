from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from db.postgres.dependancies import get_async_session
from src.messages.dependancies.messagesServiceDependancy import get_messages_service

from src.messages.services.messagesService import MessagesService


messages_router = APIRouter(
    prefix="/api/v1/messages",
    tags=["messages"],
)

 
@messages_router.post("/send-messages")
async def send_messages(
    request: Request,
    messages_service: MessagesService = Depends(get_messages_service),
    session: AsyncSession = Depends(get_async_session)
):
    return await messages_service.send_messages(request, session)

