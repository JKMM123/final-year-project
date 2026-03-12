from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from db.postgres.dependancies import get_async_session

from src.auth.services.authService import AuthService
from src.auth.dependancies.authServiceDependancy import get_auth_service



auth_router = APIRouter(
    prefix="/api/v1/auth",
    tags=["auth"],
)


@auth_router.post("/login")
async def login(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    session: AsyncSession = Depends(get_async_session)
):
    return await auth_service.login(request,session)


@auth_router.post("/logout")
async def logout(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    session: AsyncSession = Depends(get_async_session)
):
    return await auth_service.logout(request, session)


@auth_router.get("/me")
async def get_me(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    return await auth_service.get_me(request)


@auth_router.get("/refresh")
async def refresh(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    session: AsyncSession = Depends(get_async_session)
):
    return await auth_service.refresh(request, session)


@auth_router.get('/validate-token')
async def validate_token(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    session: AsyncSession = Depends(get_async_session)
):
    return await auth_service.validate_token(request, session)


@auth_router.post('/reset-password')
async def reset_password(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    session: AsyncSession = Depends(get_async_session)
):
    return await auth_service.reset_password(request, session)


@auth_router.post('/send-otp')
async def send_otp(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    session: AsyncSession = Depends(get_async_session)
):
    return await auth_service.send_otp(request, session)


@auth_router.post('/verify-otp')
async def verify_otp(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    session: AsyncSession = Depends(get_async_session)
):
    return await auth_service.verify_otp(request, session)