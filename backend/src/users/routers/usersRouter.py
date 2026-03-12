from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from db.postgres.dependancies import get_async_session

from src.users.dependancies.usersServiceDependancy import get_users_service
from src.users.services.usersService import UsersService



users_router = APIRouter(
    prefix="/api/v1/users",
    tags=["users"],
)

 
@users_router.post("/create")
async def create_user(
    request: Request,
    users_service: UsersService = Depends(get_users_service),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Endpoint to create a new user.
    """
    return await users_service.create_user(request, session)


@users_router.get("/search")
async def search_users(
    request: Request,
    users_service: UsersService = Depends(get_users_service),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Endpoint to list all users.
    """
    return await users_service.search_users(request, session)


@users_router.get("/{user_id}")
async def get_user(
    request: Request,
    users_service: UsersService = Depends(get_users_service),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Endpoint to retrieve a user by ID.
    """
    return await users_service.get_user(request, session)


@users_router.put("/{user_id}")
async def update_user(
    request: Request,
    users_service: UsersService = Depends(get_users_service),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Endpoint to update a user by ID.
    """
    return await users_service.update_user(request, session)

@users_router.delete("/{user_id}")
async def delete_user(
    request: Request,
    users_service: UsersService = Depends(get_users_service),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Endpoint to delete a user by ID.
    """
    return await users_service.delete_user(request, session)

 
