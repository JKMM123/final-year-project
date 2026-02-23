from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from db.postgres.connection import PostgresClient


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session as a dependency.
    """
    async with PostgresClient.get_async_session() as session:
        yield session