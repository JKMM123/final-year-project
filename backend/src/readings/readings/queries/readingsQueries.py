from globals.utils.logger import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select, func, delete, or_, and_, outerjoin, cast, Integer
from sqlalchemy.exc import IntegrityError
from uuid import UUID
import asyncio
from datetime import datetime, timezone, timedelta, date
from db.postgres.tables.rates import Rates
from db.postgres.tables.areas import Areas
from db.postgres.tables.meters import Meters
from db.postgres.tables.readings import Readings
from db.postgres.tables.packages import Packages
from src.readings.exceptions.exceptions import (
    ReadingNotFoundException,
    ReadingAlreadyVerifiedException,
    DuplicateReadingDateException,
    ReadingFrequencyException,
    InvalidReadingValueException,
    FixedMeterCannotHaveUsageReadingsError
)

from src.meters.exceptions.exceptions import (
    MeterNotFoundError,
    MeterInactiveError
)

from db.gcs.gcsService import GCSManager
from globals.config.config import BUCKET_NAME

class ReadingsQueries:
    def __init__(self, gcs_manager: GCSManager):
        self.gcs_manager = gcs_manager
        logger.info(f"Readings Queries initialized successfully. ")


    async def get_meter_by_id(self, session: AsyncSession, meter_id: str, usage: bool = False):
        try:
            query = select(Meters).where(Meters.meter_id == meter_id)
            result = await session.execute(query)
            meter = result.scalar_one_or_none()

            if not meter:
                logger.error(f"Meter with ID {meter_id} not found.")
                raise MeterNotFoundError()
            logger.info(f"Meter {meter_id} fetched successfully.")
            if usage and meter.package_type == 'fixed':
                raise FixedMeterCannotHaveUsageReadingsError()
            
            if meter.status == 'inactive':
                logger.error(f"Meter {meter_id} is inactive.")
                raise MeterInactiveError()

            return meter
        
        except Exception as e:
            logger.error(f"Error fetching meter by ID {meter_id}: {e}")
            raise 


    async def get_latest_reading_by_meter_id(self, session: AsyncSession, meter_id: UUID):
        try:
            query = (
                select(Readings)
                .where(Readings.meter_id == meter_id)
                .order_by(Readings.reading_date.desc())
                .limit(1)
            )
            result = await session.execute(query)
            reading = result.scalar_one_or_none()
            return reading 
        
        except Exception as e:
            logger.error(f"Error fetching latest reading for meter {meter_id}: {e}")
            raise 


    async def get_reading_by_id(self, session: AsyncSession, reading_id: str):
        query = (
            select(Readings, Meters)
            .join(Meters, Meters.meter_id == Readings.meter_id)
            .where(Readings.reading_id == reading_id)
        )
        result = await session.execute(query)
        result = result.one_or_none()
        if not result:
            raise ReadingNotFoundException()
        reading, meter = result
        reading_url = await asyncio.to_thread(
            self.gcs_manager.generate_signed_url,
            BUCKET_NAME,
            reading.blob_name,
            expiration_minutes=60,
            download=False
        )
        logger.info(f"Reading {reading_id} fetched successfully.")
        return {
            "reading_id": str(reading.reading_id),
            "meter_id": str(reading.meter_id),
            "customer_full_name": meter.customer_full_name,
            "reading_date": reading.reading_date.isoformat(),
            "current_reading": reading.current_reading,
            "previous_reading": reading.previous_reading,
            "reading_sequence": reading.reading_sequence,
            "status": reading.status,
            "reading_url": reading_url,
        }


    async def create_reading(self, session: AsyncSession, reading_data: dict, image_bytes=None):
        try:
            meter = await self.get_meter_by_id(
                session, 
                reading_data['meter_id'],
                usage=True
                )

            latest_reading = await self.get_latest_reading_by_meter_id(
                session,
                meter.meter_id
                )

            current_date = datetime.now(timezone.utc)
            
            # current_date = "2025-07-30T21:50:50.972231+00:00"
            # current_date = datetime.fromisoformat(current_date)

            # # Get the first day of the next month
            # if current_date.month == 12:
            #     next_month = current_date.replace(year=current_date.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            # else:
            #     next_month = current_date.replace(month=current_date.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)

            # three_days_before = next_month - timedelta(days=3)
            # allowed_date_range = (three_days_before.date(), next_month.date())
            # if not (allowed_date_range[0] <= current_date.date() <= allowed_date_range[1]):
            #     logger.error(f"Reading date {current_date.date()} is outside the allowed range {allowed_date_range}.")
            #     raise ReadingFrequencyException(
            #         current_reading_date= current_date.date(),
            #         allowed_date_range=allowed_date_range
            #     )
            
            if not latest_reading:
                logger.info(f"No previous reading found for meter {meter.meter_id}. Setting initial values.")
                reading_data['reading_sequence'] = 1
                reading_data['previous_reading'] = meter.initial_reading

            else:
                logger.info(f"Latest reading found for meter {meter.meter_id}. Incrementing reading sequence.")
                reading_data['reading_sequence'] = latest_reading.reading_sequence + 1
                reading_data['previous_reading'] = latest_reading.current_reading

            if not latest_reading:
                previous_reading = meter.initial_reading
            else:
                previous_reading = latest_reading.current_reading

            # check if a reading already exists for the same month and year
            day, month, year = current_date.day,current_date.month, current_date.year

            if day <= 5:
                start_date = date(
                    year=year if month > 1 else year - 1, 
                    month=month - 1 if month > 1 else 12, 
                    day=6
                    )
                end_date = date(year, month, 5)
            else:
                start_date = date(
                    year=year, 
                    month=month, 
                    day=6
                )
                end_date = date(
                    year=year if month < 12 else year + 1,
                    month=month + 1 if month < 12 else 1, 
                    day=5
                )

            logger.info(f"Fetching readings between {start_date} and {end_date}")


            reading_exists_query = await session.execute(
                    select(Readings).where(
                        Readings.meter_id == meter.meter_id,
                        Readings.reading_date >= start_date,
                        Readings.reading_date <= end_date
                )
            )
            existing_reading = reading_exists_query.scalar_one_or_none()
            if existing_reading:
                logger.error(f"Reading already exists for meter {meter.meter_id} in the date range {start_date} to {end_date}.")
                raise DuplicateReadingDateException(
                    reading_date=existing_reading.reading_date
                )
            
            current_reading = reading_data['current_reading']
            if current_reading < previous_reading:
                logger.error(f"Invalid reading value: current reading {current_reading} is less than previous reading {previous_reading}.")
                raise InvalidReadingValueException(
                    current_reading=current_reading,
                    previous_reading=previous_reading
                ) 
            
            reading_data.update(
                {
                    "usage": current_reading - previous_reading,
                    "reading_date": current_date.date(),
                    "blob_name": f"readings/{meter.customer_full_name}_{meter.customer_phone_number}_{meter.address}_{current_date.date()}.jpg",
                }
            )
            new_reading = Readings(**reading_data)
            session.add(new_reading)
            await session.commit()
            await session.refresh(new_reading)
            blob_name  = await asyncio.to_thread(
                self.gcs_manager.upload_buffer,
                bucket_name=BUCKET_NAME,
                buffer=image_bytes,
                destination_blob_name=reading_data['blob_name'],
            )
            logger.info(f"Reading {new_reading.reading_id} created successfully for meter {reading_data['meter_id']}.")
            return {
                "reading_id": str(new_reading.reading_id),
                "meter_id": str(new_reading.meter_id),
                "reading_date": new_reading.reading_date.isoformat(),
                "current_reading": new_reading.current_reading,
                "previous_reading": new_reading.previous_reading,
                "usage": new_reading.usage,
                "reading_sequence": new_reading.reading_sequence,
                "status": new_reading.status,
            }
 
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"Integrity error creating reading: {e}")
            raise

        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating reading: {e}")
            raise


    async def update_reading(self, session: AsyncSession, reading_id: str, update_data: dict):
        try:
            # fetch existing reading
            query = select(Readings).where(Readings.reading_id == reading_id)
            result = await session.execute(query)
            reading = result.scalar_one_or_none()
            if not reading:
                logger.error(f"Reading with ID {reading_id} not found.")
                raise ReadingNotFoundException()
            
            # check if reading is already verified
            if reading.status.lower() == 'verified':
                logger.error(f"Reading {reading_id} is already verified and cannot be updated.")
                raise ReadingAlreadyVerifiedException()
            
            current_reading = update_data.get('current_reading', reading.current_reading)
            usage = current_reading - reading.previous_reading
            update_data['usage'] = usage
            
            for key, value in update_data.items():
                if value is not None:
                    setattr(reading, key, value)

            await session.commit()
            await session.refresh(reading)
            logger.info(f"Reading {reading_id} updated successfully.")
            return {
                "reading_id": str(reading.reading_id),
                "meter_id": str(reading.meter_id),
                "reading_date": reading.reading_date.isoformat(),
                "current_reading": reading.current_reading,
                "previous_reading": reading.previous_reading,
                "usage": reading.usage,
                "reading_sequence": reading.reading_sequence,
                "status": reading.status,
            }

        except Exception as e:
            await session.rollback()
            logger.error(f"Error updating reading: {e}")
            raise 


    async def delete_reading(self, session: AsyncSession, reading_id: str):
        try:
            query = select(Readings).where(Readings.reading_id == reading_id)
            result = await session.execute(query)
            reading = result.scalar_one_or_none()
            if not reading:
                logger.error(f"Reading with ID {reading_id} not found.")
                raise ReadingNotFoundException()
            
            blob_name = reading.blob_name
            await session.delete(reading)
            await session.commit()
            logger.info(f"Reading {reading_id} deleted successfully.")
            # Delete the associated image from GCS
            await asyncio.to_thread(
                self.gcs_manager.delete_file,
                bucket_name=BUCKET_NAME,
                blob_name=blob_name
            )

            return True
        
        except Exception as e:
            await session.rollback()
            logger.error(f"Error deleting reading: {e}")
            raise 
 

    async def search_readings(self, session: AsyncSession, filters: dict):
        try:
            query = (
                select(Readings, Meters.customer_full_name, Meters.customer_phone_number, Areas.area_name)
                .select_from(Readings)
                .join(Meters, Meters.meter_id == Readings.meter_id)
                .join(Areas, Areas.area_id == Meters.area_id)
                )
            
            if filters.get('area_ids'):
                query = query.where(Meters.area_id.in_(filters['area_ids']))

            if filters.get('query'):
                query = query.filter(
                    or_(
                        Meters.customer_full_name.ilike(f"%{filters['query']}%"),
                        Meters.customer_phone_number.ilike(f"%{filters['query']}%")
                    )
                )

            if filters.get('status'):
                query = query.filter(Readings.status.in_(filters['status']))

            reading_date = filters.get('reading_date')
            year, month = map(int, reading_date.split('-'))

            start_date = date(
                    year=year, 
                    month=month, 
                    day=6
                )
            end_date = date(
                year=year if month < 12 else year + 1,
                month=month + 1 if month < 12 else 1, 
                day=5
            )
            logger.info(f"Filtering readings between {start_date} and {end_date}")
            
            query = query.where(
                Readings.reading_date >= start_date,
                Readings.reading_date <= end_date
            )
            
            page = filters.get('page', 1)
            limit = filters.get('limit', 10)

            total_count = select(func.count()).select_from(query.subquery())
            total_result = await session.execute(total_count)
            total_count = total_result.scalar() or 0
            total_pages = (total_count + limit - 1) // limit
            has_next = page < total_pages
            has_previous = page > 1

            query = query.limit(limit).offset((page - 1) * limit)
            result = await session.execute(query)
            results = result.all()
            
            readings_list = [
            {
                "reading_id": str(r.reading_id),
                "meter_id": str(r.meter_id),
                "customer_full_name": customer_full_name,
                "customer_phone_number": customer_phone_number,
                "reading_date": r.reading_date.isoformat(),
                "current_reading": r.current_reading,
                "previous_reading": r.previous_reading,
                "usage": r.usage,
                "reading_sequence": r.reading_sequence,
                "status": r.status,
                "area_name": area_name
            } for r, customer_full_name, customer_phone_number, area_name in results
        ]
            logger.info(f"Search completed. Found {len(readings_list)} readings.")
            logger.info(f"Total count of readings: {total_count}, Total pages: {total_pages}, Current page: {page}, Has next: {has_next}, Has previous: {has_previous}")

            return {
                "readings": readings_list,
                "pagination": {
                    "current_page": page,
                    "per_page": limit,
                    "total_items": total_count,
                    "total_pages": total_pages,
                    "has_next": has_next,
                    "has_previous": has_previous,
                    "next_page": page + 1 if has_next else None,
                    "previous_page": page - 1 if has_previous else None
                }
            }
        
        except Exception as e:
            logger.error(f"Error searching readings: {e}")
            raise


    async def get_readings_summary(self, session: AsyncSession, reading_date: str):
        """
        Returns the meters that have readings to be taken with pagination.
        """
        try:
            year, month = map(int, reading_date.split('-'))
            
            
            # Get meters that already have readings in the specified date range
            meters_with_readings_query = (
                select(Readings.meter_id.distinct())
                .where(
                    cast(func.extract("month", Readings.reading_date), Integer) == month,
                    cast(func.extract("year", Readings.reading_date), Integer) == year,
                )
            )
            meters_with_readings_result = await session.execute(meters_with_readings_query)
            meters_with_readings_ids = set(row for row in meters_with_readings_result.scalars().all())
            

            # Get total count for pagination
            count_query = select(func.count(Meters.meter_id)).where(
                and_(
                    Meters.status == 'active',
                    Meters.package_type == 'usage',
                    Meters.meter_id.notin_(meters_with_readings_ids) if meters_with_readings_ids else True
                )
            )


            # Query for verified readings in the specified date range
            verified_readings_query = (
                select(func.count(Readings.reading_id).label('verified_readings_count'))
                .join(Meters, Meters.meter_id == Readings.meter_id)
                .where(
                    and_(
                        cast(func.extract("month", Readings.reading_date), Integer) == month,
                        cast(func.extract("year", Readings.reading_date), Integer) == year,
                        Readings.status == 'verified',
                        Meters.status == 'active'
                    )
                )
            )
            
            # Query for pending readings in the specified date range
            pending_readings_query = (
                select(func.count(Readings.reading_id).label('pending_readings_count'))
                .join(Meters, Meters.meter_id == Readings.meter_id)
                .where(
                    and_(
                        cast(func.extract("month", Readings.reading_date), Integer) == month,
                        cast(func.extract("year", Readings.reading_date), Integer) == year,
                        Readings.status == 'pending',
                        Meters.status == 'active'
                    )
                )
            )

            # Get total active meters count
            total_active_query = select(func.count(Meters.meter_id)).where(
                Meters.status == 'active',
                Meters.package_type == 'usage'
            )

            # Execute count and paginated queries in parallel
            count_result = await session.execute(count_query)
            verified_readings_result = await session.execute(verified_readings_query)
            pending_readings_result = await session.execute(pending_readings_query)
            total_active_result = await session.execute(total_active_query)
            
            total_meters_needing_readings = count_result.scalar() or 0
            verified_readings_count = verified_readings_result.scalar() or 0
            pending_readings_count = pending_readings_result.scalar() or 0
            total_active_meters = total_active_result.scalar() or 0
            
            logger.info(f"Readings summary for {reading_date} fetched successfully.")
            
            return {
                "reading_date": reading_date,
                "total_active_meters": total_active_meters,
                "meters_with_readings": len(meters_with_readings_ids),
                "meters_needing_readings": total_meters_needing_readings,
                "verified_readings_count": verified_readings_count,
                "pending_readings_count": pending_readings_count,
            }

        except Exception as e:
            logger.error(f"Error fetching readings summary: {e}")
            raise


    async def verify_all_readings(self, session: AsyncSession, reading_date: str, verified_by: str):
        try:
            year, month = map(int, reading_date.split('-'))
            
            # Calculate date range based on the billing period logic used elsewhere
            start_date = date(year, month, 6)
            
            # Calculate next month and year for end date
            if month == 12:
                end_month = 1
                end_year = year + 1
            else:
                end_month = month + 1
                end_year = year
            
            end_date = date(end_year, end_month, 5)
            
            logger.info(f"Verifying all readings between {start_date} and {end_date}")
            
            # Count how many readings will be updated
            count_query = select(func.count(Readings.reading_id)).where(
                and_(
                    Readings.reading_date >= start_date,
                    Readings.reading_date <= end_date,
                    Readings.status == 'pending'
                )
            )
            
            count_result = await session.execute(count_query)
            readings_to_verify = count_result.scalar() or 0
            
            if readings_to_verify == 0:
                logger.info(f"No pending readings found for period {reading_date}")
                return {
                    "message": f"No pending readings found for period {reading_date}",
                    "verified_count": 0,
                    "reading_date": reading_date
                }
            
            # Update all pending readings to verified
            update_query = (
                update(Readings)
                .where(
                    and_(
                        Readings.reading_date >= start_date,
                        Readings.reading_date <= end_date,
                        Readings.status == 'pending'
                    )
                )
                .values(
                    status='verified',
                    updated_by=verified_by,
                )
            )
            
            result = await session.execute(update_query)
            verified_count = result.rowcount
            
            await session.commit()
            
            logger.info(f"Successfully verified {verified_count} readings for period {reading_date}")
            
            return {
                "message": f"Successfully verified {verified_count} readings for period {reading_date}",
                "verified_count": verified_count,
                "reading_date": reading_date,
                "date_range": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            }

        except Exception as e:
            await session.rollback()
            logger.error(f"Error verifying all readings: {e}")
            raise

        
    

