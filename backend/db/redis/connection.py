import redis.asyncio as redis
from typing import Optional
from globals.config.config import (
    REDIS_HOST,
    REDIS_DB,
    REDIS_PASSWORD,
    REDIS_PORT,
    REDIS_USERNAME,
)
from globals.utils.logger import logger


class RedisManager:
    _instance: Optional[redis.Redis] = None

    @classmethod
    async def get_instance(cls) -> redis.Redis:
        try:
            print("Initializing Redis connection...")
            if cls._instance is None:
                cls._instance = redis.Redis(
                    username=REDIS_USERNAME,
                    host=REDIS_HOST,
                    port=REDIS_PORT,
                    password=REDIS_PASSWORD,
                    db=REDIS_DB,
                    decode_responses=True,
                    retry_on_timeout=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                # Test the connection with a ping
                await cls._instance.ping()
                logger.info("Redis connection initialized and verified successfully.")
            return cls._instance

        except Exception as e:
            logger.error(f"Error initializing or verifying Redis connection: {e}")
            raise e

    @classmethod
    async def close(cls):
        try:
            if cls._instance:
                await cls._instance.close()
                cls._instance = None
                logger.info("Redis connection closed.")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")
            raise
