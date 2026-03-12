from globals.utils.logger import logger
from db.postgres.base import Base
from db.postgres.tables.refresh_tokens import RefreshTokens
from db.postgres.tables.users import Users
from db.postgres.tables.rates import Rates
from db.postgres.tables.packages import Packages
from db.postgres.tables.meters import Meters
from db.postgres.tables.readings import Readings
from db.postgres.tables.bills import Bills
from db.postgres.tables.areas import Areas
from db.postgres.tables.whatsapp_session import WhatsAppSession
from db.postgres.tables.templates import Templates
from db.postgres.tables.otp import OTP
from db.postgres.tables.fixes import Fixes
from db.postgres.tables.passwordReset import PasswordReset
from db.postgres.tables.payments import Payments

from db.postgres.connection import PostgresClient

async def create_all_entities(client: PostgresClient):
    """
    Initialize database and seed initial data
    
    Args:
        client: The PostgreSQL client class to use for database operations
    """
    try:
        if not client._async_engine:
            logger.error("Database engine not initialized")
            return False

        async with client._async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
            
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False