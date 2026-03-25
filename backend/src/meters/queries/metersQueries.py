from globals.utils.logger import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select, func, delete, or_, and_, cast, Integer
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta, date
from db.postgres.tables.packages import Packages
from db.postgres.tables.readings import Readings
from db.postgres.tables.meters import Meters
from db.postgres.tables.areas import Areas
from globals.utils.timezoneHelper import TimezoneHelper

from globals.config.config import BUCKET_NAME
from src.meters.exceptions.exceptions import (
    MeterNotFoundError,
    CustomerIdentityAddressAlreadyExistsError,
    MeterInUseError,
    InitialReadingRequiredError
)
from globals.config.config import FRONT_END_URL

from src.areas.exceptions.exceptions import AreaNotFoundException

from src.packages.exceptions.exceptions import PackagesNotFoundError

from src.meters.services.qrCodeService import QRCodeService
from db.gcs.gcsService import GCSManager

from concurrent.futures import ThreadPoolExecutor
import asyncio


class MetersQueries:
    def __init__(self, gcs_manager: GCSManager):
        self.gcs_manager = gcs_manager
        self.MAX_CONCURRENT_UPLOADS = 5 
        logger.info(f"Meters Queries initialized successfully. ")


    async def get_area_by_id(self, session: AsyncSession, area_id: str):
        try:
            query = select(Areas).where(Areas.area_id == area_id)
            result = await session.execute(query)
            area = result.scalar_one_or_none()
            if not area:
                logger.error(f"Area with ID {area_id} not found.")
                raise AreaNotFoundException()
            
            logger.info(f"Area {area.area_id} fetched successfully.")
            return area
        
        except Exception as e:
            logger.error(f"Error getting area by ID {area_id}: {e}")
            raise e


    async def get_package_by_id(self, session: AsyncSession, package_id: str):
        try:
            query = select(Packages).where(Packages.package_id == package_id)
            result = await session.execute(query)
            pkg = result.scalar_one_or_none()
            if not pkg:
                logger.error(f"Package with ID {package_id} not found.")
                raise PackagesNotFoundError()
            
            logger.info(f"Package {pkg.package_id} fetched successfully.")
            return pkg
        
        except Exception as e:
            logger.error(f"Error getting package by ID {package_id}: {e}")
            raise e


    async def get_meter_by_id(self, session: AsyncSession, meter_id: str):
        try:
            query = (
                select(Meters, Packages.amperage, Areas.area_name, Areas.elevation)
                .join(Packages, Meters.package_id == Packages.package_id)
                .join(Areas, Meters.area_id == Areas.area_id)
                .where(
                    Meters.meter_id == meter_id
                )
            )
            result = await session.execute(query)
            row = result.one_or_none()
            if not row:
                logger.error(f"Meter with ID {meter_id} not found.")
                raise MeterNotFoundError()
            meter, amperage, area_name, elevation = row

            logger.info(f"Meter {meter.meter_id} fetched successfully.")
            return {
                "meter_id": str(meter.meter_id),
                "customer_full_name": meter.customer_full_name,
                "customer_phone_number": meter.customer_phone_number,
                "initial_reading": float(meter.initial_reading) if meter.initial_reading is not None else None,
                "status": meter.status,
                "area_name": area_name,
                "area_id": str(meter.area_id),
                "elevation": elevation,
                "address": meter.address,
                "package_id": str(meter.package_id),
                "amperage": amperage,
                "package_type": meter.package_type,
            }
        
        except Exception as e:
            logger.error(f"Error getting meter by ID {meter_id}: {e}")
            raise


    async def create_meter(self, session: AsyncSession, meter_data: dict):
        try:
            # Check if package exists
            package = await self.get_package_by_id(session, meter_data['package_id'])
            area = await self.get_area_by_id(session, meter_data['area_id'])
            blob_name = f"meters/{meter_data.get('customer_full_name').replace(' ', '_')}_{meter_data.get('address').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"

            meter_data.update({
                "blob_name": blob_name,
            })

            new_meter = Meters(**meter_data)
            session.add(new_meter)
            await session.commit()
            await session.refresh(new_meter)
            # Generate QR code for the meter
            qr_data = f"{FRONT_END_URL}/readings/capture-reading/{new_meter.meter_id}"
            qr_image = QRCodeService.generate_qr_with_label(
                data=qr_data, 
                label=f"customer: {meter_data.get('customer_full_name')}, address: {meter_data.get('address')}"
                )
            blob_name  = await asyncio.to_thread(
                self.gcs_manager.upload_buffer,
                bucket_name=BUCKET_NAME,
                buffer=qr_image,
                destination_blob_name=blob_name
            )
            
            logger.info(f"Meter {new_meter.meter_id} created successfully.")
            return {
                "meter_id": str(new_meter.meter_id),
                "customer_full_name": new_meter.customer_full_name,
                "initial_reading": float(new_meter.initial_reading) if new_meter.initial_reading is not None else None,
                "status": new_meter.status,
                "area_name": area.area_name,
                "elevation": area.elevation,
                "address": new_meter.address,
                "area_id": str(new_meter.area_id),
                "package_id": str(new_meter.package_id),
                "amperage": package.amperage,
                "package_type": new_meter.package_type,
            }
        
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"Integrity error creating meter: {e}")
            error_message = str(e.orig)
            if "uq_customer_identity_address" in error_message:
                raise CustomerIdentityAddressAlreadyExistsError(
                    customer_full_name=meter_data.get('customer_full_name'),
                    customer_phone_number=meter_data.get('customer_phone_number'),
                    address=meter_data.get('address')
                )
            else:
                raise e
            
        except (
            PackagesNotFoundError,
            AreaNotFoundException
        ):
            raise

        except Exception as e:
            await session.rollback()
            await asyncio.to_thread(
                self.gcs_manager.delete_file,
                bucket_name=BUCKET_NAME,
                blob_name=blob_name
            )
            logger.error(f"Error creating meter: {e}")
            raise 

    
    async def update_meter(self, session: AsyncSession, meter_id: str, update_data: dict):
        try:
            # Fetch existing meter
            meter = select(Meters).where(Meters.meter_id == meter_id)
            result = await session.execute(meter)
            meter = result.scalar_one_or_none()
            if not meter:
                raise MeterNotFoundError()
            
            # Check if package exists if package_id is being updated
            package = await self.get_package_by_id(session, update_data['package_id'])

            # Check if area exists if area_id is being updated
            area = await self.get_area_by_id(session, update_data['area_id'])

            if (meter.package_type == "usage" and update_data.get('package_type') == "usage"):
                update_data.update({
                    "initial_reading": meter.initial_reading
                })

                
            # Update fields
            for key, value in update_data.items():
                setattr(meter, key, value)

            session.add(meter)
            await session.commit()
            await session.refresh(meter)
            logger.info(f"Meter {meter.meter_id} updated successfully.")
            return {
                "meter_id": str(meter.meter_id),
                "customer_full_name": meter.customer_full_name,
                "initial_reading": float(meter.initial_reading) if meter.initial_reading is not None else None,
                "status": meter.status,
                "area_name": area.area_name,
                "area_id": str(meter.area_id),
                "elevation": area.elevation,
                "address": meter.address,
                "package_id": str(meter.package_id),
                "amperage": package.amperage,
                "package_type": meter.package_type,
            }
        
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"Integrity error updating meter: {e}")
            error_message = str(e.orig)
            if "uq_customer_identity_address" in error_message:
                raise CustomerIdentityAddressAlreadyExistsError(
                    customer_full_name=update_data.get('customer_full_name'),
                    customer_phone_number=update_data.get('customer_phone_number'),
                    address=update_data.get('address')
                )
            else:
                raise e
        
        except Exception as e:
            await session.rollback()
            logger.error(f"Error updating meter {meter_id}: {e}")
            raise e


    async def delete_meter(self, session: AsyncSession, meter_id: str):
        try:
            # Fetch existing meter
            meter = select(Meters).where(Meters.meter_id == meter_id)
            result = await session.execute(meter)
            meter = result.scalar_one_or_none()
            if not meter:
                raise MeterNotFoundError()
            
            # Delete meter
            await session.delete(meter)
            await session.commit()
            logger.info(f"Meter {meter_id} deleted successfully.")

            try:
                success = await asyncio.to_thread(
                    self.gcs_manager.delete_file,
                    BUCKET_NAME,
                    meter.blob_name
                )
            except Exception as e:
                logger.error(f"Error deleting QR code for meter {meter_id}: {e}")
                
            return True
        
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"Integrity error deleting meter: {e}")
            raise MeterInUseError()
        
        except Exception as e:
            await session.rollback()
            logger.error(f"Error deleting meter {meter_id}: {e}")
            raise e


    async def search_meters(self, session: AsyncSession, search_params: dict):
        try:
            reading_date = search_params.get('reading_date', None)
            if reading_date:
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
            else:
                current_date = TimezoneHelper.get_business_current_time().date()
                day = current_date.day
                year = current_date.year
                month = current_date.month

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

                
            # Latest reading within [start_date, end_date] per meter
            current_reading_ranked = (
                select(
                    Readings.meter_id.label('meter_id'),
                    Readings.current_reading.label('current_reading'),
                    Readings.reading_date.label('reading_date'),
                    func.row_number()
                    .over(
                        partition_by=Readings.meter_id,
                        order_by=Readings.reading_date.desc()
                    )
                    .label('rn')
                )
                .where(
                    and_(
                        Readings.reading_date >= start_date,
                        Readings.reading_date <= end_date
                    )
                )
            ).subquery('current_reading_ranked')

            current_reading_subquery = (
                select(
                    current_reading_ranked.c.meter_id,
                    current_reading_ranked.c.current_reading
                )
                .where(current_reading_ranked.c.rn == 1)
            ).subquery('current_reading_subquery')

            # Last reading BEFORE start_date per meter (previous reading)
            previous_reading_ranked = (
                select(
                    Readings.meter_id.label('meter_id'),
                    Readings.current_reading.label('previous_reading'),
                    Readings.reading_date.label('reading_date'),
                    func.row_number()
                    .over(
                        partition_by=Readings.meter_id,
                        order_by=Readings.reading_date.desc()
                    )
                    .label('rn')
                )
                .where(Readings.reading_date < start_date)
            ).subquery('previous_reading_ranked')

            previous_reading_subquery = (
                select(
                    previous_reading_ranked.c.meter_id,
                    previous_reading_ranked.c.previous_reading
                )
                .where(previous_reading_ranked.c.rn == 1)
            ).subquery('previous_reading_subquery')
            
            # Main query with left joins to get meter info along with readings
            query = (
                select(
                    Meters,
                    Packages.amperage,
                    Areas.area_name,
                    current_reading_subquery.c.current_reading,
                    func.coalesce(
                        previous_reading_subquery.c.previous_reading,
                        Meters.initial_reading
                    ).label('previous_reading')
                )
                .join(Packages, Meters.package_id == Packages.package_id)
                .join(Areas, Meters.area_id == Areas.area_id)
                .outerjoin(
                    current_reading_subquery,
                    Meters.meter_id == current_reading_subquery.c.meter_id
                )
                .outerjoin(
                    previous_reading_subquery,
                    Meters.meter_id == previous_reading_subquery.c.meter_id
                )
            )
            
            # Apply filters based on search parameters
            if search_params.get('query'):
                query = query.where(
                    or_(
                        Meters.customer_full_name.ilike(f"%{search_params['query']}%"),
                        Meters.customer_phone_number.ilike(f"%{search_params['query']}%")
                    )
                )
            if search_params.get('area_ids'):
                query = query.where(Meters.area_id.in_(search_params['area_ids']))

            if search_params.get('package_ids'):
                query = query.where(Meters.package_id.in_(search_params['package_ids']))

            if search_params.get('package_type'):
                query = query.where(Meters.package_type == search_params['package_type'])

            if search_params.get('status'):
                status = search_params['status']
                if "awaiting_reading" in status or "have_reading" in status:
                    meters_with_readings_query = (
                        select(Readings.meter_id.distinct())
                        .where(
                            Readings.reading_date >= start_date,
                            Readings.reading_date <= end_date
                        )
                    )
                    meters_with_readings_result = await session.execute(meters_with_readings_query)
                    meters_with_readings_ids = [row for row in meters_with_readings_result.scalars().all()]
                    logger.info(f"Found {len(meters_with_readings_ids)} meters with readings in the period {start_date} to {end_date}.")

                if "awaiting_reading" in status:
                    # Handle case when no meters have readings (empty list)
                    if meters_with_readings_ids:
                        query = query.where(
                            and_(
                                Meters.meter_id.not_in(meters_with_readings_ids),
                                Meters.status == 'active',
                                Meters.package_type == 'usage'
                            )
                        )
                    else:
                        # If no meters have readings, all active usage meters are awaiting readings
                        query = query.where(
                            and_(
                                Meters.status == 'active',
                                Meters.package_type == 'usage'
                            )
                        )

                elif "have_reading" in status:
                    # Only show meters that actually have readings
                    if meters_with_readings_ids:
                        query = query.where(
                            and_(
                                Meters.meter_id.in_(meters_with_readings_ids),
                                Meters.status == 'active',
                                Meters.package_type == 'usage'
                            )
                        )
                    else:
                        # If no meters have readings, return empty result
                        query = query.where(False)

                else:
                    query = query.where(Meters.status.in_(status))

            total_count_query = select(func.count()).select_from(query.subquery())
            total_count_result = await session.execute(total_count_query)
            total_count = total_count_result.scalar()

            page = search_params.get('page', 1)
            limit = search_params.get('limit', 10)

            total_pages = (total_count + limit - 1) // limit
            has_next = page < total_pages
            has_previous = page > 1
            offset = (page - 1) * limit
            query = query.offset(offset).limit(limit)

            result = await session.execute(query)
            result = result.all()

            meters_list = [
                {
                    "meter_id": str(meter.meter_id),
                    "customer_full_name": meter.customer_full_name,
                    "customer_phone_number": meter.customer_phone_number,
                    "initial_reading": float(meter.initial_reading) if meter.initial_reading is not None else None,
                    "status": meter.status,
                    "address": meter.address,
                    "area_id": str(meter.area_id),
                    "area_name": area_name,
                    "package_id": str(meter.package_id),
                    "amperage": amperage,
                    "package_type": meter.package_type,
                    "current_reading": float(current_reading) if current_reading is not None else None,
                    "previous_reading": float(previous_reading) if previous_reading is not None else float(meter.initial_reading) if meter.initial_reading is not None else None
                } for meter, amperage, area_name, current_reading, previous_reading in result
            ]
            logger.info(f"Found {len(meters_list)} meters matching search criteria.")

            return {
                "meters": meters_list,
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
            logger.error(f"Error searching meters: {e}")
            raise e


    async def get_qr_code(self, session: AsyncSession, meter_id: str):
        try:
            meter = select(Meters).where(Meters.meter_id == meter_id)
            result = await session.execute(meter)
            meter = result.scalar_one_or_none()
            if not meter:
                raise MeterNotFoundError()

            blob_name = meter.blob_name
            signed_url = await asyncio.to_thread(
                self.gcs_manager.generate_signed_url,
                bucket_name=BUCKET_NAME,
                blob_name=blob_name,
                expiration_minutes=60
            )
            return signed_url

        except Exception as e:
            logger.error(f"Error getting QR code for meter {meter_id}: {e}")
            raise e


    async def get_all_packages_query(self, session: AsyncSession):
        try:
            query = select(Packages)
            result = await session.execute(query)
            packages = result.scalars().all()
            if not packages:
                logger.info("No packages found.")
                return {}

            logger.info(f"Found {len(packages)} packages.")
            packages_dict = {package.amperage: package.package_id for package in packages}
            logger.info(f'found: {len(packages_dict)} packages with amperage as key')
            return packages_dict

        except Exception as e:
            logger.error(f"Error fetching all packages: {e}")
            raise e
        

    async def get_all_areas_query(self, session: AsyncSession):
        try:
            query = select(Areas)
            result = await session.execute(query)
            areas = result.scalars().all()
            if not areas:
                logger.info("No areas found.")
                return {}

            logger.info(f"Found {len(areas)} areas.")
            areas_dict = {area.area_name: area.area_id for area in areas}
            return areas_dict
        
        except Exception as e:
            logger.error(f"Error fetching all areas: {e}")
            raise e


    async def get_all_customers_names_phone_and_addresses_query(self, session: AsyncSession):
        try:
            query = select(
                Meters.customer_full_name,
                Meters.customer_phone_number,
                Meters.address
            )
            result = await session.execute(query)
            customers = result.all()
            if not customers:
                logger.info("No active customers found.")
                return []

            customers_list = [
                {
                    "customer_full_name": customer.customer_full_name,
                    "customer_phone_number": customer.customer_phone_number,
                    "address": customer.address
                } for customer in customers
            ]
            logger.info(f"Found {len(customers_list)} active customers.")
            return customers_list
        
        except Exception as e:
            logger.error(f"Error fetching active customers: {e}")
            raise e


    async def get_qr_codes(self, session: AsyncSession):
        try:
            query = select(Meters.meter_id, Meters.blob_name).where(Meters.status == 'active')
            result = await session.execute(query)
            blob_names = result.all()
            if not blob_names:
                logger.info("No QR codes found.")
                return []

            
            zip_file_signed_url = await asyncio.to_thread(
                self.gcs_manager.create_qr_zip_and_signed_url,
                bucket_name=BUCKET_NAME,
                qr_blob_names=[row.blob_name for row in blob_names],
                expiration_minutes=60*24
            )
            return zip_file_signed_url

        except Exception as e:
            logger.error(f"Error fetching QR codes: {e}")
            raise e


    async def upload_qr(self, meter_data, created_by):
        qr_data = f"Customer: {meter_data.get('customer_full_name')}, Address: {meter_data.get('address')}"
        qr_image = QRCodeService.generate_qr_with_label(
            data=qr_data,
            label=f"customer: {meter_data.get('customer_full_name')}, address: {meter_data.get('address')}"
        )
        blob_name = f"meters/{meter_data.get('customer_full_name').replace(' ', '_')}_{meter_data.get('address').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.png"
        blob_name = await asyncio.to_thread(
            self.gcs_manager.upload_buffer,
            bucket_name=BUCKET_NAME,
            buffer=qr_image,
            destination_blob_name=blob_name
        )

        meter_data.update({
            "blob_name": blob_name,
            "created_by": created_by,
            "updated_by": created_by,
        })
        return Meters(**meter_data), blob_name
    

    async def insert_meters_from_file_query(self, session: AsyncSession, meters_data: list, created_by: str):
        blob_names = []
        try:
            semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_UPLOADS)

            async def sem_upload(meter_data):
                async with semaphore:
                    return await self.upload_qr(meter_data, created_by)

            tasks = [sem_upload(m) for m in meters_data]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            new_meters = []
            for result in results:
                if isinstance(result, Exception):
                    raise result
                meter, blob_name = result
                new_meters.append(meter)
                blob_names.append(blob_name)

            session.add_all(new_meters)
            await session.commit()

            return {
                "successful_inserts": len(new_meters),
                "failed_inserts": 0
            }

        except Exception as e:
            logger.error(f"Error inserting meters: {e}")
            await session.rollback()
            await asyncio.to_thread(
                self.gcs_manager.delete_files,
                bucket_name=BUCKET_NAME,
                blob_names=blob_names
            )
            raise


    async def delete_meters_query(self, session: AsyncSession, meter_ids: list[str]):
        try:
            query = delete(Meters).where(Meters.meter_id.in_(meter_ids))
            result = await session.execute(query)
            if result.rowcount == 0:
                logger.error(f"No meters found with IDs: {meter_ids}")
                raise MeterNotFoundError()

            await session.commit()
            logger.info(f"Deleted {result.rowcount} meters successfully.")
            return True
        
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"Integrity error deleting meter: {e}")
            raise MeterInUseError()

        except Exception as e:
            await session.rollback()
            logger.error(f"Error deleting meters: {e}")
            raise e



