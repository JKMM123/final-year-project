from globals.utils.logger import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select, func, delete, or_, and_
from sqlalchemy.orm import Session

from db.postgres.tables.whatsapp_session import WhatsAppSession

from src.messages.exceptions.exceptions import (
    WhatsAppSessionNotFoundError,
    WhatsAppSessionAlreadyExistsError
)

class WhatsAppSessionQueries:
    def __init__(self):
        logger.info(f"Session Queries initialized successfully. ")


    async def create_session(self, session_id, api_key: str, name:str, phone_number:str,webhook_secret:str, session: AsyncSession):
        try:
            # Check if a session already exists
            existing_session = select(WhatsAppSession).where(WhatsAppSession.id == 1)
            result = await session.execute(existing_session)
            session_data = result.scalar_one_or_none()
            if session_data:
                logger.warning(f"Session with ID {session_id} already exists.")
                raise WhatsAppSessionAlreadyExistsError()

            new_session = WhatsAppSession(
                name=name,
                phone_number=phone_number,
                session_id=session_id,
                api_key=api_key,
                webhook_secret=webhook_secret
                )
            
            session.add(new_session)
            await session.commit()
            logger.info(f"Session {new_session.id} created successfully.")
            return new_session
        
        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating session: {e}")
            raise


    async def get_session(self,session: AsyncSession):
        try:
            get_session_data_query = select(WhatsAppSession).where(WhatsAppSession.id == 1)
            result = await session.execute(get_session_data_query)
            session_data = result.scalar_one_or_none()
            if not session_data:
                logger.warning(f"Session with ID 1 not found.")
                raise WhatsAppSessionNotFoundError()
            
            return session_data
        
        except Exception as e:
            logger.error(f"Error retrieving session: {e}")
            raise 


    async def delete_session(self, session: AsyncSession):
        try:
            # Check if a session already exists
            existing_session = select(WhatsAppSession).where(WhatsAppSession.id == 1)
            result = await session.execute(existing_session)
            session_data = result.scalar_one_or_none()
            if not session_data:
                logger.warning(f"Session with ID 1 not found.")
                raise WhatsAppSessionNotFoundError()
            
            await session.delete(session_data)
            await session.commit()
            logger.info(f"Session with ID 1 deleted successfully.")
            return

        except Exception as e:
            await session.rollback()
            logger.error(f"Error deleting session: {e}")
            raise


    def get_session_sync(self,session: Session):
        try:
            get_session_data_query = select(WhatsAppSession).where(WhatsAppSession.id == 1)
            result = session.execute(get_session_data_query)
            session_data = result.scalar_one_or_none()
            if not session_data:
                logger.warning(f"Session with ID 1 not found.")
                raise WhatsAppSessionNotFoundError()
            
            return session_data
        
        except Exception as e:
            logger.error(f"Error retrieving session sync: {e}")
            raise
