from src.messages.services.messagesService import MessagesService
from fastapi import Request



async def get_messages_service(request: Request) -> MessagesService:
    return request.app.state.messages_service
