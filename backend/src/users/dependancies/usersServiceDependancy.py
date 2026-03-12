from fastapi import Request
from src.users.services.usersService import UsersService



async def get_users_service(request: Request) -> UsersService:
    return request.app.state.users_service
