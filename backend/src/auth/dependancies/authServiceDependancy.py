from src.auth.services.authService import AuthService
from fastapi import Request



async def get_auth_service(request: Request) -> AuthService:
    return request.app.state.auth_service
