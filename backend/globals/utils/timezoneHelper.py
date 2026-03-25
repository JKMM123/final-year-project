from datetime import datetime, timezone
from typing import Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from globals.utils.logger import logger
from sqlalchemy import select
from zoneinfo import ZoneInfo


class TimezoneHelper:
    business_timezone: ZoneInfo = ZoneInfo("Asia/Beirut")  

    @classmethod
    def get_business_current_time(cls) -> datetime:
        """Get current time in business timezone"""
        return datetime.now(cls.business_timezone)

    @classmethod
    def convert_utc_to_business(cls, utc_dt: datetime) -> datetime:
        """Convert UTC datetime to business timezone"""
        try:
            if utc_dt.tzinfo is None:
                utc_dt = utc_dt.replace(tzinfo=ZoneInfo("UTC"))
            return utc_dt.astimezone(cls.business_timezone)
        except Exception as e:
            logger.error(f"Error converting UTC to business timezone: {e}")
            return utc_dt

    @classmethod
    def convert_business_to_utc(cls, business_dt: datetime) -> datetime:
        """Convert business timezone datetime to UTC (returns naive datetime for DB)"""
        try:
            # If datetime is naive, assume it's in business timezone
            if business_dt.tzinfo is None:
                business_dt = business_dt.replace(tzinfo=cls.business_timezone)

            utc_dt = business_dt.astimezone(ZoneInfo("UTC"))
            logger.debug(f"Converted {cls.business_timezone} {business_dt} to UTC: {utc_dt}")

            # Return as NAIVE datetime for database storage/comparison
            return utc_dt.replace(tzinfo=None)

        except Exception as e:
            logger.error(f"Error converting business timezone to UTC: {e}")
            return business_dt.replace(tzinfo=None)
        

    @classmethod
    def to_utc_naive(cls, dt: datetime) -> datetime:
        """Convert any aware datetime to naive UTC, or return as-is if already naive."""
        if dt is None:
            return None
        if dt.tzinfo is not None:
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt