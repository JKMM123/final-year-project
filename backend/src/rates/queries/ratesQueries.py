from globals.utils.logger import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select, func, delete, or_, and_
from sqlalchemy.exc import IntegrityError   
import calendar
from db.postgres.tables.rates import Rates

from src.rates.exceptions.exec import (
    RatesException,
    RateNotFoundError
)
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

class RatesQueries:
    def __init__(self):
        self.timezone = ZoneInfo("Asia/Beirut")
        logger.info(f"Rates Queries initialized successfully. ")


    def _calculate_billing_period(self, effective_date):
        """Calculate billing period for a given date (6th to 5th of next month)"""
        year = effective_date.year
        month = effective_date.month
        day = effective_date.day
        
        if day < 6:
            if month == 1:
                billing_year = year - 1
                billing_month = 12
            else:
                billing_year = year
                billing_month = month - 1
        else:
            billing_year = year
            billing_month = month
            
        return billing_year, billing_month


    async def _check_billing_period_exists(self, session: AsyncSession, effective_date, exclude_rate_id=None):
        """Check if rates already exist for the billing period containing the input date"""
        billing_year, billing_month = self._calculate_billing_period(effective_date)
        
        start_date = date(billing_year, billing_month, 6)
        
        if billing_month == 12:
            end_year = billing_year + 1
            end_month = 1
        else:
            end_year = billing_year
            end_month = billing_month + 1
            
        end_date = date(end_year, end_month, 5)
        
        # Query for existing rates in this billing period
        query = select(Rates).where(
            and_(
                Rates.date >= start_date,
                Rates.date <= end_date
            )
        )
        
        # Exclude current rate if updating
        if exclude_rate_id:
            query = query.where(Rates.rate_id != exclude_rate_id)
            
        result = await session.execute(query)
        existing_rates = result.scalars().all()
        
        return existing_rates, f"{billing_year}-{billing_month:02d}"

    
    async def create_rates(self, session: AsyncSession, rate_data: dict):
        try:

            year, month = map(int, rate_data.get("effective_date").split('-'))
            effective_date = date(year, month, 28)

            existing_rates, billing_period = await self._check_billing_period_exists(session, effective_date)
            
            if existing_rates:
                existing_date = existing_rates[0].date.isoformat()
                logger.error(f"Rates already exist for billing period {billing_period}. Existing rate dated: {existing_date}")
                raise RatesException(f"Rates already exist for billing period {billing_period}. Existing rate dated: {existing_date}")
            
            rate_data["date"] = effective_date
            del rate_data["effective_date"]
            new_rates = Rates(**rate_data)
            session.add(new_rates)
            await session.commit()
            await session.refresh(new_rates)
            logger.info("Rates created successfully.")
            return {
                "rate_id": str(new_rates.rate_id),
                "mountain_kwh_rate": new_rates.mountain_kwh_rate,
                "coastal_kwh_rate": new_rates.coastal_kwh_rate,
                "dollar_rate": new_rates.dollar_rate,
                "fixed_sub_hours": new_rates.fixed_sub_hours,
                "fixed_sub_rate": new_rates.fixed_sub_rate,
                "date": new_rates.date.isoformat(),
            }

        except IntegrityError as e:
            await session.rollback()
            error_info = str(e.orig)
            if "uq_rates_date" in error_info:
                logger.error(f"Rates for date '{rate_data.get('date')}' already exist.")
                raise RatesException("Rates for this date already exist.")
            else:
                logger.error(f"Integrity error creating rates: {error_info}")
                raise

        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating rates: {e}")
            raise


    async def update_rates(self, session: AsyncSession, rate_data):
        """
        Update rates in the database.
        """
        try:
            get_rates = select(Rates).where(Rates.rate_id == rate_data["rate_id"])
            result = await session.execute(get_rates)
            rates = result.scalar_one_or_none()
            if not rates:
                logger.error(f"Rates with ID {rate_data['rate_id']} not found.")
                raise RatesException("Rate not found.")

            rates.mountain_kwh_rate = rate_data["mountain_kwh_rate"]
            rates.coastal_kwh_rate = rate_data["coastal_kwh_rate"]
            rates.dollar_rate = rate_data["dollar_rate"]
            rates.fixed_sub_hours = rate_data["fixed_sub_hours"]
            rates.fixed_sub_rate = rate_data["fixed_sub_rate"]
            rates.updated_by = rate_data.get("updated_by")
            session.add(rates)
            await session.commit()
            await session.refresh(rates)
            
            logger.info("Rates updated successfully.")
            return {
                "rate_id": str(rates.rate_id),
                "mountain_kwh_rate": rates.mountain_kwh_rate,
                "coastal_kwh_rate": rates.coastal_kwh_rate,
                "dollar_rate": rates.dollar_rate,
                "fixed_sub_hours": rates.fixed_sub_hours,
                "fixed_sub_rate": rates.fixed_sub_rate,
            }
                

        except Exception as e:
            logger.error(f"Error updating rates: {e}")
            await session.rollback()
            raise


    async def delete_rates(self, session: AsyncSession, rate_id: str):
        """
        Delete rates from the database.
        """
        try:
            get_rates = select(Rates).where(Rates.rate_id == rate_id)
            result = await session.execute(get_rates)
            rates = result.scalar_one_or_none()
            if not rates:
                logger.error(f"Rates with ID {rate_id} not found.")
                raise RatesException("Rate not found.")
            
            await session.delete(rates)
            await session.commit()
            logger.info(f"Rates with ID {rate_id} deleted successfully.")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting rates: {e}")
            await session.rollback()
            raise


    async def get_rates_by_id(self, session: AsyncSession, rate_id: str):
        """
        Fetch rates by their unique ID.
        """   
        try:            
            get_rates_query = select(Rates).where(Rates.rate_id == rate_id)
            result = await session.execute(get_rates_query)
            rates = result.scalar_one_or_none()
            
            if not rates:
                logger.error(f"No rates found with ID {rate_id}")
                raise RateNotFoundError(f"No rates found")
            
            logger.info(f"Rates fetched successfully for ID {rate_id}")
            return {
                "rate_id": str(rates.rate_id),
                "mountain_kwh_rate": rates.mountain_kwh_rate,
                "coastal_kwh_rate": rates.coastal_kwh_rate,
                "dollar_rate": rates.dollar_rate,
                "fixed_sub_hours": rates.fixed_sub_hours,
                "fixed_sub_rate": rates.fixed_sub_rate,
                "date": rates.date.isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error fetching rates for ID {rate_id}: {e}")
            raise
        

    async def list_all_rates_by_year(self, session: AsyncSession, year: int):
        """
        List all rates for a given year.
        """   
        try:            
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)
            
            list_rates_query = select(Rates).where(
                and_(
                    Rates.date >= start_date,
                    Rates.date <= end_date
                )
            ).order_by(Rates.date.desc())
            
            result = await session.execute(list_rates_query)
            rates = result.scalars().all()
            
            if not rates:
                logger.error(f"No rates found for year {year}")
                return []
            
            logger.info(f"Rates fetched successfully for year {year}")
            return [
                {
                    "rate_id": str(rate.rate_id),
                    "mountain_kwh_rate": rate.mountain_kwh_rate,
                    "coastal_kwh_rate": rate.coastal_kwh_rate,
                    "dollar_rate": rate.dollar_rate,
                    "rate_month": self._get_billing_month_name(rate.date),
                    "fixed_sub_hours": rate.fixed_sub_hours,
                    "fixed_sub_rate": rate.fixed_sub_rate,
                }
                for rate in rates
            ]
            
        except Exception as e:
            logger.error(f"Error fetching rates for year {year}: {e}")
            raise


    def _get_billing_month_name(self, rate_date):
        """
        Convert rate date to billing period month name.
        Billing period: 6th of month to 5th of next month.
        
        Args:
            rate_date (date): The actual rate date
            
        Returns:
            str: Month name representing the billing period
        """
        year = rate_date.year
        month = rate_date.month
        day = rate_date.day
        
        if day < 6:
            if month == 1:
                billing_month = 12
                billing_year = year - 1
            else:
                billing_month = month - 1
                billing_year = year
        else:
            billing_month = month
            billing_year = year
        
        month_name = calendar.month_name[billing_month]
        
        return month_name


    async def get_rates_by_date(self, date_input, session: AsyncSession):
        """
        Fetch rates for the billing period that contains the given date.
        Uses 6th of month to 6th of next month billing period logic.
        """   
        try:            
            # Extract year and month from the date input
            year, month = map(int, date_input.split('-'))
            
            # Calculate date range based on 6th-to-6th billing period logic
            # If we're looking for rates for month X, we need rates between:
            # 6th of month X to 6th of month X+1
            start_date = date(year, month, 6)
            
            # Calculate next month and year for end date
            if month == 12:
                end_month = 1
                end_year = year + 1
            else:
                end_month = month + 1
                end_year = year
            
            end_date = date(end_year, end_month, 6)
            
            logger.info(f"Fetching rates between {start_date} and {end_date} for billing period {year}-{month:02d}")
            
            # Get rates that fall within this billing period (6th to 6th)
            get_rates_query = select(Rates).where(
                and_(
                    Rates.date >= start_date,
                    Rates.date < end_date  # Use < instead of <= to exclude the 6th of next month
                )
            ).order_by(Rates.date.desc())  # Get the most recent rate in the period
            
            result = await session.execute(get_rates_query)
            rates = result.scalar_one_or_none()
            
            if not rates:
                logger.error(f"No rates found for billing period {year}-{month:02d} (between {start_date} and {end_date})")
                raise RateNotFoundError(f"No rates found for {date_input}")
            
            logger.info(f"Rates fetched successfully for billing period {year}-{month:02d}")
            return {
                "rate_id": str(rates.rate_id),
                "mountain_kwh_rate": rates.mountain_kwh_rate,
                "coastal_kwh_rate": rates.coastal_kwh_rate,
                "dollar_rate": rates.dollar_rate,
                "fixed_sub_hours": rates.fixed_sub_hours,
                "fixed_sub_rate": rates.fixed_sub_rate,
                "date": rates.date.isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error fetching rates for date {date_input}: {e}")
            raise

