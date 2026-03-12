from sqlalchemy.future import select
from db.postgres.tables.users import Users
from globals.utils.logger import logger
from db.postgres.connection import PostgresClient
from globals.config.config import SYSTEM_USERNAME, SYSTEM_USER_PHONE_NUMBER, SYSTEM_PASSWORD
from globals.utils.hashingHelper import HashingHelper




async def seed_system_user_in_pg(): 
    async with PostgresClient.get_async_session() as db:
        try:
            result = await db.execute(
                select(Users).where(
                    Users.username == SYSTEM_USERNAME,
                    Users.phone_number == SYSTEM_USER_PHONE_NUMBER,
                    Users.role == "system"
                )
            )
            exists = result.scalars().first()
            if exists:
                logger.info(f"System user {SYSTEM_USERNAME} already exists in Postgres.")
                return exists
            else:
                hashed_password = HashingHelper.generate_hash(SYSTEM_PASSWORD)
                user = Users(
                    username=SYSTEM_USERNAME,
                    role="system",
                    phone_number=SYSTEM_USER_PHONE_NUMBER,
                    password_hash=hashed_password
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
                logger.info(f"System user {SYSTEM_USERNAME} seeded to Postgres successfully.")
                return user

        
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error seeding system user to Postgres: {e}")
    