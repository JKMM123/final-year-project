from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, Session

from globals.config.config import ASYNC_POSTGRES_DATABASE_URL
from globals.utils.logger import logger
from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine, text  
from contextlib import contextmanager, asynccontextmanager


class PostgresClient:
    """
    Asynchronous PostgreSQL client using SQLAlchemy.
    """
    _async_engine = None
    _sync_engine = None
    _async_session_factory = None
    _sync_session_factory = None
    _is_async_available = False
    _is_sync_available = False

    @classmethod
    async def init_async_engine(cls):
        """Initialize the database engine and check availability"""
        try:
            pool_size = 10
            max_overflow = 5
            pool_timeout = 20
            pool_recycle = 1800

            cls._async_engine = create_async_engine(
                ASYNC_POSTGRES_DATABASE_URL,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_timeout=pool_timeout,
                pool_recycle=pool_recycle,
                echo=False,
                connect_args={"server_settings": {"timezone": "UTC"}}
            )
            
            cls._async_session_factory = async_sessionmaker(
                bind=cls._async_engine,
                expire_on_commit=False,
                class_=AsyncSession,
                autoflush=False,
                autocommit=False
            )
            success = await cls.check_async_engine_availability()
            return success
            
        except Exception as e:
            cls._is_async_available = False
            logger.error(f"Error initializing async engine:  {str(e)}")
            raise 


    @classmethod
    def init_sync_engine(cls):
        """Initialize the database engine and check availability"""
        sync_db_url = ASYNC_POSTGRES_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        try:
            pool_size = 10
            max_overflow = 5
            pool_timeout = 20
            pool_recycle = 1800

            cls._sync_engine = create_engine(
                sync_db_url,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_timeout=pool_timeout,
                pool_recycle=pool_recycle,
                echo=False,
                connect_args={"options": "-c timezone=utc"}
            )

            cls._sync_session_factory = sessionmaker(
                bind=cls._sync_engine,
                expire_on_commit=False,
                class_=Session,
                autoflush=False,
                autocommit=False
            )
            success = cls.check_sync_engine_availability()
            return success
            
        except Exception as e:
            cls._is_sync_available = False
            logger.error(f"Error initializing sync engine: {str(e)}")
            raise 


    @classmethod
    async def check_async_engine_availability(cls) -> bool:
        """Check if database is available by executing a test query"""
        if not cls._async_engine:
            logger.warning("Cannot check async engine availability: engine not initialized")
            cls._is_async_available = False
            return False
            
        try:
            session = cls._async_session_factory()
            try:
                await session.execute(text("SELECT 1"))
                await session.commit()
                cls._is_async_available = True
                logger.info("Async Database connection verified successfully")
                return True
            except SQLAlchemyError as e:
                cls._is_async_available = False
                logger.error(f"Async Database availability check failed: {str(e)}")
                return False
            finally:
                await session.close()
        except Exception as e:
            cls._is_async_available = False
            logger.error(f"Error checking database availability: {str(e)}")
            return False
        

    @classmethod
    def check_sync_engine_availability(cls) -> bool:
        """Check if database is available by executing a test query"""
        if not cls._sync_engine:
            logger.warning("Cannot check sync engine availability: engine not initialized")
            cls._is_sync_available = False
            return False
            
        try:
            session = cls._sync_session_factory()
            try:
                session.execute(text("SELECT 1"))
                session.commit()
                cls._is_sync_available = True
                logger.info("Sync Database connection verified successfully")
                return True
            except SQLAlchemyError as e:
                cls._is_sync_available = False
                logger.error(f"Sync Database availability check failed: {str(e)}")
                return False
            finally:
                session.close()
        except Exception as e:
            cls._is_sync_available = False
            logger.error(f"Error checking database availability: {str(e)}")
            return False


    @classmethod
    async def close_async_engine(cls):
        """Close the database engine and connections"""
        if cls._async_engine:
            await cls._async_engine.dispose()
            cls._async_engine = None
            cls._async_session_factory = None
            cls._is_async_available = False
            logger.info("Async Database engine closed successfully")


    @classmethod
    def close_sync_engine(cls):
        """Close the database engine and connections"""
        if cls._sync_engine:
            cls._sync_engine.dispose()
            cls._sync_engine = None
            cls._sync_session_factory = None
            cls._is_sync_available = False
            logger.info("Sync Database engine closed successfully")


    @classmethod
    @asynccontextmanager
    async def get_async_session(cls) -> AsyncGenerator[AsyncSession, None]:
        """
        Session generator for dependency injection.
        
        Usage as FastAPI dependency:
        async def endpoint(session: AsyncSession = Depends(PostgresClient.get_session)):
            ...
        """
        if cls._async_session_factory is None:
            logger.error("Database engine not initialized")
            raise Exception("Database engine not initialized. Call init_engine first.")
        
        session = cls._async_session_factory()
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Async Database error: {str(e)}")
            raise
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()


    @classmethod
    @contextmanager
    def get_sync_session(cls) -> Generator[Session, None, None]:
        """
        Session generator for dependency injection.

        Usage as FastAPI dependency:
        async def endpoint(session: AsyncSession = Depends(PostgresClient.get_session)):
            ...
        """
        if cls._sync_session_factory is None:
            logger.error("Database engine not initialized")
            raise Exception("Database engine not initialized. Call init_engine first.")

        session = cls._sync_session_factory()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Sync Database error: {str(e)}")
            raise
        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected error in Sync Database session: {str(e)}")
            raise
        finally:
            session.close()




    

