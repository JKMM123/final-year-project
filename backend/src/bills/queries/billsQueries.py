from db.postgres.tables import bills
from globals.utils.logger import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select, func, delete, or_, and_, text, case, cast, Integer
from db.postgres.tables.bills import Bills
from db.postgres.tables.readings import Readings
from db.postgres.tables.packages import Packages
from db.postgres.tables.meters import Meters
from db.postgres.tables.rates import Rates
from db.postgres.tables.areas import Areas
from db.postgres.tables.fixes import Fixes
from db.postgres.tables.payments import Payments
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from typing import Dict, List
from uuid import uuid4
from globals.utils.timezoneHelper import TimezoneHelper
from src.bills.exceptions.exceptions import (
    BillNotFoundError,
    MessagesSendingError,
    DeletePaidBillError,
    BillsGenerationRestrictionError
)
import math
import calendar
from src.rates.exceptions.exec import (
    RateNotFoundError
)
from src.meters.exceptions.exceptions import NoActiveMetersError, MeterNotFoundError
from src.readings.exceptions.exceptions import (
    NoReadingsFoundForActiveMetersError,
    MissingReadingsForActiveMetersError,
    UnverifiedReadingsError
)
from datetime import date
from db.gcs.gcsService import GCSManager
from globals.config.config import BUCKET_NAME
import asyncio

from src.rates.queries.ratesQueries import RatesQueries


class BillsQueries:
    def __init__(self):
        self.gcs_manager = GCSManager()
        self.rates_queries = RatesQueries()
        logger.info("Bills Queries initialized successfully.")
     

    async def get_bill(self, session: AsyncSession, bill_id: str):
        try:
            get_bill_query = select(Bills).where(Bills.bill_id == bill_id)
            result = await session.execute(get_bill_query)
            bill = result.scalar_one_or_none()

            if not bill:
                logger.error(f"Bill with ID {bill_id} not found.")
                raise BillNotFoundError()
            try:
                
                bill_url = await asyncio.to_thread(
                    self.gcs_manager.generate_signed_url,
                    BUCKET_NAME,
                    bill.blob_name,
                    expiration_minutes=15,
                    download=False
                )
            except Exception as e:
                logger.error(f"Error generating signed URL for bill ID {bill_id}: {e}")
                bill_url = None

            return {
                "bill_id": str(bill.bill_id),
                "bill_number": bill.bill_number,
                "amount_due_lbp": str(bill.amount_due_lbp),
                "amount_due_usd": str(bill.amount_due_usd),
                "total_paid_lbp": str(bill.total_paid_lbp),
                "total_paid_usd": str(bill.total_paid_usd),
                "status": bill.status,
                "bill_url": bill_url
            }

        except Exception as e:
            logger.error(f"Error fetching bill with ID {bill_id}: {e}")
            raise


    async def search_bills(self, session: AsyncSession, filters:dict):
        try:
            query = select(Bills,Meters.customer_full_name).join(
                Meters, Bills.meter_id == Meters.meter_id
            ) 
            if "due_date" in filters:
                year, month = map(int, filters["due_date"].split('-'))
                year=year if month < 12 else year + 1
                month=month + 1 if month < 12 else 1
                query = query.where(Bills.due_date == date(year, month, 1))

            if "status" in filters and filters["status"]:
                query = query.where(Bills.status.in_(filters["status"]))

            if "payment_method" in filters and filters["payment_method"]:
                query = query.where(Bills.payment_method.in_(filters["payment_method"]))

            if "query" in filters and filters["query"]:
                search_term = f"%{filters['query']}%"
                query = query.where(
                    or_(
                        Meters.customer_full_name.ilike(search_term),
                        Meters.customer_phone_number.ilike(search_term)
                    )
                )
            
            page = filters.get('page', 1)
            limit = filters.get('limit', 10)
            offset = (page - 1) * limit

            total_count = select(func.count()).select_from(query.subquery())
            total_result = await session.execute(total_count)
            total_count = total_result.scalar() or 0

            query = query.limit(limit).offset(offset)
            result = await session.execute(query)
            result = result.all()

            total_pages = (total_count + limit - 1) // limit
            has_next = page < total_pages
            has_previous = page > 1

            bills_list = [
                {
                    "bill_id": str(bill.bill_id),
                    "bill_number": bill.bill_number,
                    "amount_due_lbp": str(bill.amount_due_lbp),
                    "amount_due_usd": str(bill.amount_due_usd),
                    "total_paid_lbp": str(bill.total_paid_lbp),
                    "total_paid_usd": str(bill.total_paid_usd),
                    "status": bill.status,
                    "customer_full_name": customer_name
            }
                for bill, customer_name in result
            ]
            logger.info(f"Found {len(bills_list)} bills matching the search criteria.")
            
            return {
                "bills": bills_list,
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
            logger.error(f"Error searching bills: {e}")
            raise


    async def delete_bill(self, session: AsyncSession, bill_id: str):
        try:
            get_bill_to_delete = select(Bills).where(Bills.bill_id == bill_id)
            result = await session.execute(get_bill_to_delete)
            bill = result.scalar_one_or_none()
            if not bill:
                logger.error(f"Bill with ID {bill_id} not found.")
                raise BillNotFoundError()

            if bill.status in ['partially_paid', 'paid']:
                logger.error(f"Bill with ID {bill_id} is already {bill.status}.")
                status = "paid" if bill.status == "paid" else "partially paid"
                raise DeletePaidBillError(status)

            await session.execute(delete(Bills).where(Bills.bill_id == bill_id))
            try:
                await asyncio.to_thread(self.gcs_manager.delete_file, BUCKET_NAME, f"bills/{bill_id}.jpg")
            
            except Exception as e:
                logger.error(f"Error deleting bill file from GCS for bill ID {bill_id}: {e}")
                pass

            await session.commit()
            logger.info(f"Bill with ID {bill_id} deleted successfully.")
            
            return True

        except Exception as e:
            await session.rollback()
            logger.error(f"Error deleting bill with ID {bill_id}: {e}")
            raise 


    async def update_bill(self, session: AsyncSession, bill_id:str, data:dict):
        try:
            get_bill_query = select(Bills).where(Bills.bill_id == bill_id)
            result = await session.execute(get_bill_query)
            bill = result.scalar_one_or_none()
            if not bill:
                logger.error(f"Bill with ID {bill_id} not found.")
                raise BillNotFoundError()
            
            data.update({
                "payment_date": datetime.now(timezone.utc).date() if data.get("status") == "paid" else None,
            })
            # Update bill fields
            for key, value in data.items():
                setattr(bill, key, value)
            await session.commit()
            await session.refresh(bill)

            logger.info(f"Bill with ID {bill_id} updated successfully.")
            return {
                "bill_id": str(bill.bill_id),
                "amount": bill.amount_due_lbp,
                "amount_due_usd": bill.amount_due_usd,
                "due_date": bill.due_date.isoformat() if bill.due_date else None,
                "status": bill.status,
                "payment_date": bill.payment_date.isoformat() if bill.payment_date else None,
                "payment_method": bill.payment_method if bill.payment_method else None  
            }
        
        except Exception as e:
            logger.error(f"Error updating bill with ID {bill_id}: {e}")
            raise


    async def generate_bills(self, session: AsyncSession, creator_id: str, billing_date: str, rate_id:str, force_missing_meter: bool = False, force_unverified_readings: bool = False):
        bills = []
        metrics = {
            "total_active_meters": 0,
            "fixed_package_meters": 0,
            "usage_based_meters": 0,
            "meters_with_readings": 0,
            "verified_readings": 0,
            "unverified_readings": 0,
            "meters_without_readings": 0,
            "bills_created": 0,
            "bills_already_exist": 0,
            "skipped_meters": 0,
            "errors": []
        }
        try:
            logger.info(f"Starting bill generation process, creator_id: {creator_id}, force_missing_meter: {force_missing_meter}, force_unverified_readings: {force_unverified_readings}")

            current_date = billing_date
            year, month = map(int, current_date.split('-'))

            logger.info(f"Date validation passed. Current date: {year}-{month:02d}")

            # Get all active meters
            active_meters_query = await session.execute(select(Meters).where(Meters.status == "active"))
            active_meters = active_meters_query.scalars().all()
            active_meter_ids = [meter.meter_id for meter in active_meters]

            metrics["total_active_meters"] = len(active_meters)
            logger.info(f"Found {metrics['total_active_meters']} active meters")

            if not active_meter_ids:
                logger.error("No active meters found.")
                raise NoActiveMetersError()

            due_date = datetime(
                year=year if month < 12 else year + 1,
                month=month + 1 if month < 12 else 1,
                day=1,
                tzinfo=timezone.utc
                )

            # Check which bills already exist for this due date
            logger.info(f"Checking for existing bills for due date: {due_date.date()}")
            existing_bills_query = await session.execute(
                select(Bills.meter_id).where(Bills.due_date == due_date.date(), Bills.meter_id.is_not(None))
            )
            existing_bill_meter_ids = set(existing_bills_query.scalars().all())
            
            metrics["bills_already_exist"] = len(existing_bill_meter_ids)
            logger.info(f"Found {metrics['bills_already_exist']} existing bills for this billing period")

            # Filter out meters that already have bills
            meters_needing_bills = [meter for meter in active_meters if meter.meter_id not in existing_bill_meter_ids]

            logger.info(f"Need to generate bills for {len(meters_needing_bills)} meters (excluding existing bills)")

            generated_bill_ids = []
            if not meters_needing_bills:
                logger.info("All active meters already have bills for this period")
                return {
                    "success": True,
                    "message": f"All bills already exist for {year}-{month:02d}",
                    "metrics": metrics,
                    "billing_period": f"{year}-{month:02d}",
                    "due_date": due_date.date().isoformat(),
                }

            fixed_package_meters = [meter for meter in meters_needing_bills if meter.package_type == "fixed"]
            usage_based_meters = [meter for meter in meters_needing_bills if meter.package_type == "usage"]
            metrics["fixed_package_meters"] = len(fixed_package_meters)
            metrics["usage_based_meters"] = len(usage_based_meters)

            readings = []
            if usage_based_meters:
                usage_based_meter_ids = [meter.meter_id for meter in usage_based_meters]
                logger.info(f"Fetching readings for {len(usage_based_meters)} usage-based meters for billing period: {year}-{month:02d}")

                start_date = date(year, month, 6)
                # Calculate next month and year
                if month == 12:
                    end_month = 1
                    end_year = year + 1
                else:
                    end_month = month + 1
                    end_year = year
                
                end_date = date(end_year, end_month, 5)
                logger.info(f"Fetching readings between {start_date} and {end_date}")

                readings_query = await session.execute(
                        select(Readings).where(
                            Readings.meter_id.in_(usage_based_meter_ids),
                            Readings.reading_date >= start_date,
                            Readings.reading_date <= end_date
                    )
                )
                readings = readings_query.scalars().all()
            
            meters_with_readings = set(r.meter_id for r in readings)
            metrics["meters_with_readings"] = len(meters_with_readings)
            metrics["meters_without_readings"] = len(usage_based_meter_ids) - len(meters_with_readings)
            logger.info(f"Found readings for {metrics['meters_with_readings']} usage-based meters")
            logger.info(f"{metrics['meters_without_readings']} usage-based meters are missing readings")

            # Analyze readings status
            verified_readings = [r for r in readings if r.status == "verified"]
            unverified_readings = [r for r in readings if r.status == "pending"]

            metrics["verified_readings"] = len(verified_readings)
            metrics["unverified_readings"] = len(unverified_readings)
            logger.info(f"Readings analysis: {metrics['verified_readings']} verified, "
                    f"{metrics['unverified_readings']} unverified, "
                    f"{metrics['meters_without_readings']} missing (usage-based only)")

            # Validate missing meters (only for usage-based meters that need bills)
            if metrics["meters_without_readings"] > 0 and not force_missing_meter:
                usage_based_meter_ids = [meter.meter_id for meter in usage_based_meters]
                missing_meter_ids = set(usage_based_meter_ids) - meters_with_readings
                logger.error(f"Missing readings for {metrics['meters_without_readings']} usage-based meters: {list(missing_meter_ids)}")
                return {
                    "success": False,
                    "message": f"Missing readings for {metrics['meters_without_readings']} usage-based meters for billing period {year}-{month:02d}",
                    "metrics": metrics,
                    "billing_period": f"{year}-{month:02d}",
                    "due_date": due_date.date().isoformat(),
                    "missing_meters_count": metrics["meters_without_readings"]
                }

            # Check if usage-based meters have readings
            if usage_based_meters and not readings:
                logger.error(f"No readings found for usage-based meters needing bills for date {year}-{month:02d}")
                return {
                    "success": False,
                    "message": f"No readings found for usage-based meters for billing period {year}-{month:02d}",
                    "metrics": metrics,
                    "billing_period": f"{year}-{month:02d}",
                    "due_date": due_date.date().isoformat(),
                    "missing_meters_count": len(usage_based_meters),
                }
            
            if usage_based_meters and not verified_readings:
                logger.error(f"No verified readings found for usage-based meters needing bills for date {year}-{month:02d}")
                return {
                    "success": False,
                    "message": f"No verified readings found for usage-based meters for billing period {year}-{month:02d}",
                    "metrics": metrics,
                    "billing_period": f"{year}-{month:02d}",
                    "due_date": due_date.date().isoformat(),
                    "unverified_readings_count": len(unverified_readings),
                }

            
            # Validate unverified readings
            if unverified_readings and not force_unverified_readings:
                unverified_meter_ids = [r.meter_id for r in unverified_readings]
                logger.error(f"Found {len(unverified_readings)} unverified readings for meters: {unverified_meter_ids}")
                return {
                    "success": False,
                    "message": f"Found {len(unverified_readings)} unverified readings for billing period {year}-{month:02d}",
                    "metrics": metrics,
                    "billing_period": f"{year}-{month:02d}",
                    "due_date": due_date.date().isoformat(),
                    "unverified_readings_count": len(unverified_readings)
                }
                
            # Get rates
            logger.info("Fetching current rates...")
            rates = await self.rates_queries.get_rates_by_id(
                rate_id=rate_id, 
                session=session
                )

            meters_with_verified_readings = set(reading.meter_id for reading in verified_readings)
            billable_meters = set()
            
            # Add fixed package meters (they don't need readings)
            for meter in fixed_package_meters:
                billable_meters.add(meter.meter_id)
            
            # Add usage-based meters with verified readings
            billable_meters.update(meters_with_verified_readings)
            logger.info(f"Total billable meters (fixed + usage with verified readings): {len(billable_meters)}")

            unique_package_ids = set()
            unique_areas_ids = set()
            
            # Get unique package and areas IDs for meters with verified readings that need bills
            for meter in meters_needing_bills:
                if meter.meter_id in billable_meters:
                    unique_package_ids.add(meter.package_id)
                    unique_areas_ids.add(meter.area_id)

            logger.info(f"Fetching {len(unique_package_ids)} unique packages...")
            get_meters_packages = select(Packages).where(Packages.package_id.in_(unique_package_ids))
            packages = await session.execute(get_meters_packages)
            packages = packages.scalars().all()

            packages_dict = {pkg.package_id: pkg for pkg in packages}

            logger.info(f'fetching areas for {len(unique_areas_ids)} unique areas...')

            get_meters_areas = select(Areas).where(Areas.area_id.in_(unique_areas_ids))
            areas = await session.execute(get_meters_areas)
            areas = areas.scalars().all()

            areas_dict = {area.area_id: area for area in areas}

            # Get fixes for verified readings
            logger.info(f'Fetching fixes for {len(billable_meters)} verified readings...')
            get_fixes = select(Fixes).where(
                and_(
                    Fixes.meter_id.in_(billable_meters),
                    cast(func.extract("month", Fixes.fix_date), Integer) == month,
                    cast(func.extract("year", Fixes.fix_date), Integer) == year
            ))
            fixes = await session.execute(get_fixes)
            fixes = fixes.scalars().all()

            fixes_dict = defaultdict(list)
            for fix in fixes:
                fixes_dict[fix.meter_id].append(fix)

            # Generate bills for meters that need them
            logger.info("Starting bill creation process...")
            for meter in meters_needing_bills:
                if meter.meter_id not in billable_meters:
                    metrics["skipped_meters"] += 1
                    logger.debug(f"Skipping meter {meter.meter_id} - no verified reading")
                    continue
                    
                try:
                    package = packages_dict.get(meter.package_id)
                    area = areas_dict.get(meter.area_id)
                    meter_fixes = fixes_dict.get(meter.meter_id, [])

                    # Calculate total fix cost for this meter
                    total_fix_cost = sum(int(fix.cost) for fix in meter_fixes)

                    package_type = meter.package_type

                    if package_type == "fixed":
                        amount_due_lbp = int(package.fixed_fee) + total_fix_cost * int(rates.get('dollar_rate')) 
                        amount_due_usd = amount_due_lbp / int(rates.get('dollar_rate')) 

                    else:
                        reading = next((r for r in verified_readings if r.meter_id == meter.meter_id), None)

                        if area.elevation < 700:
                            usage = int(reading.usage) if reading.usage else 0
                            amount_due_lbp = (usage * int(rates.get('coastal_kwh_rate'))) + int(package.activation_fee) + (total_fix_cost * int(rates.get('dollar_rate')))

                        else:
                            usage = int(reading.usage) if reading.usage else 0
                            amount_due_lbp = (usage * int(rates.get('mountain_kwh_rate'))) + int(package.activation_fee) + (total_fix_cost * int(rates.get('dollar_rate')))

                        amount_due_usd = amount_due_lbp / int(rates.get('dollar_rate'))
                    bill_id = uuid4()
                    bill = Bills(
                        bill_id=bill_id,
                        meter_id=meter.meter_id,
                        amount_due_lbp=amount_due_lbp,
                        amount_due_usd= round(amount_due_usd, 2),        #math.ceil(amount_due_usd) if (amount_due_usd - int(amount_due_usd)) > 0.5 else math.floor(amount_due_usd),
                        due_date=due_date.date(),
                        created_by=creator_id,
                        rate_id=rate_id,
                    )
                    bills.append(bill)
                    metrics["bills_created"] += 1
                    generated_bill_ids.append(bill_id)

                except Exception as e:
                    error_msg = f"Error creating bill for meter {meter.meter_id}: {str(e)}"
                    logger.error(error_msg)
                    metrics["errors"].append(error_msg)
                    metrics["skipped_meters"] += 1

            # Save new bills to database
            if bills:
                logger.info(f"Saving {len(bills)} new bills to database...")
                try:
                    session.add_all(bills)
                    await session.commit()
                    logger.info("Bills successfully saved to database")
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Error saving bills to database: {str(e)}")
                    raise
            else:
                logger.warning("No new bills were created")

            # Calculate success rates
            total_meters_processed = len(meters_needing_bills)
            success_rate = (metrics["bills_created"] / total_meters_processed) * 100 if total_meters_processed > 0 else 0
            overall_completion = ((metrics["bills_created"] + metrics["bills_already_exist"]) / metrics["total_active_meters"]) * 100

            logger.info("Bill generation completed", extra={
                "metrics": metrics,
                "success_rate_percent": round(success_rate, 2),
                "overall_completion_percent": round(overall_completion, 2),
                "billing_period": f"{year}-{month:02d}",
                "due_date": due_date.date().isoformat()
            })

            return {
                "success": True,
                "message": f"Generated {metrics['bills_created']} new bills for {year}-{month:02d}. {metrics['bills_already_exist']} bills already existed.",
                "metrics": metrics,
                "billing_period": f"{year}-{month:02d}",
                "due_date": due_date.date().isoformat(),
                "overall_completion_percent": round(overall_completion, 2),
                "generated_bill_ids": generated_bill_ids
            }
        
        except RateNotFoundError:
            raise

        except Exception as e:
            await session.rollback()
            logger.error(f"Unexpected error in generate_bills: {str(e)}", extra={"metrics": metrics})
            raise


    async def get_bills_full_data_for_due_date(self, session: AsyncSession, billing_date: str, bill_ids: list=None, rate_id: str = None) -> List[Dict]:
        """Return full payload for all bills with the given due_date."""
        try:

            year, month = map(int, billing_date.split('-'))
            bill_year=year if month < 12 else year + 1
            bill_month=month + 1 if month < 12 else 1
            due_date = date(
                year=bill_year, 
                month=bill_month, 
                day=1
                )
            
            if rate_id is None:
                rates = await self.rates_queries.get_rates_by_date(
                    date_input=billing_date,
                    session=session
                )

            else:
                rates = await self.rates_queries.get_rates_by_id(
                    rate_id=rate_id,
                    session=session
                )
            if not rates:
                logger.error("Rates not found.")
                raise RateNotFoundError()

            unpaid_bills_query = await session.execute(
                select(
                    Bills.meter_id,
                    func.sum(Bills.amount_due_lbp - Bills.total_paid_lbp).label('total_unpaid_lbp'),
                    func.sum(Bills.amount_due_usd - Bills.total_paid_usd).label('total_unpaid_usd')
                )
                .where(
                    and_(
                        Bills.due_date < due_date,
                        Bills.status.in_(['unpaid', 'partially_paid'])  # Only unpaid bills
                    )
                )
                .group_by(Bills.meter_id)
            )

            arrears_by_meter = {}
            for row in unpaid_bills_query:
                arrears_by_meter[row.meter_id] = {
                    'total_unpaid_lbp': int(row.total_unpaid_lbp) if row.total_unpaid_lbp else 0.0,
                    'total_unpaid_usd': int(row.total_unpaid_usd) if row.total_unpaid_usd else 0.0
                }

            query = (
                select(Bills, Meters, Areas, Packages, Readings)
                .select_from(Bills)
                .join(Meters, Bills.meter_id == Meters.meter_id)
                .join(Areas, Meters.area_id == Areas.area_id)
                .join(Packages, Meters.package_id == Packages.package_id)
                .outerjoin(
                    Readings,
                    and_(
                        Readings.meter_id == Bills.meter_id,
                        func.extract("month", Readings.reading_date) == month,
                        func.extract("year", Readings.reading_date) == year,
                        Readings.status == "verified",
                    )
                )
            )
            if bill_ids is not None and len(bill_ids) > 0:
                query = query.where(Bills.bill_id.in_(bill_ids))
                logger.info(f"Filtering by {len(bill_ids)} specific bill IDs for billing period {year}-{month:02d}")
            else:
                query = query.where(Bills.due_date == due_date)
                logger.info(f"Filtering by due_date: {due_date.isoformat()} for billing period {year}-{month:02d}")

            rs = await session.execute(query)
            rows = rs.all()
            if not rows:
                logger.info(f"No bills found for due_date {due_date.isoformat()}")
                return []

            # Batch fetch fixes for all meters in this batch and period
            meter_ids = [row.Bills.meter_id for row in rows]
            fixes_rs = await session.execute(
                select(Fixes).where(
                    and_(
                        Fixes.meter_id.in_(meter_ids),
                        func.extract("month", Fixes.fix_date) == month,
                        func.extract("year", Fixes.fix_date) == year,
                    )
                )
            )
            fixes_by_meter = defaultdict(list)
            for fx in fixes_rs.scalars().all():
                fixes_by_meter[fx.meter_id].append(fx)

            result: List[Dict] = []
            for row in rows:
                bill, meter, area, package, reading = row
                fx_list = fixes_by_meter.get(bill.meter_id, [])
                total_fixes = sum(int(f.cost) for f in fx_list if f.cost)

                # Common fields
                bill_due_date_str = bill.due_date.strftime("%d/%m/%Y") if bill.due_date else None
                amperage = int(package.amperage) if package.amperage is not None else None
                meter_arrears = arrears_by_meter.get(bill.meter_id, {'total_unpaid_lbp': 0.0, 'total_unpaid_usd': 0.0})

                if meter.package_type == "usage":
                    activation_fee = int(package.activation_fee) if package.activation_fee else 0.0
                    kwh_rate = int(rates.get('coastal_kwh_rate')) if (area.elevation is not None and area.elevation < 700) else int(rates.get('mountain_kwh_rate'))
                    reading_month = reading.reading_date.strftime("%m/%Y") if reading and reading.reading_date else None

                    total = (int(bill.amount_due_lbp) if bill.amount_due_lbp else 0.0) - total_fixes - activation_fee

                    item = {
                        "package_type": "usage",
                        "bill_id": bill.bill_id,
                        "bill_due_date": bill_due_date_str,
                        "bill_number": bill.bill_number,
                        "usd_value": int(bill.amount_due_usd) if bill.amount_due_usd is not None else 0.0,
                        "lbp_value": int(bill.amount_due_lbp) if bill.amount_due_lbp is not None else 0.0,

                        "customer_name": meter.customer_full_name,
                        "customer_phone_number": meter.customer_phone_number,
                        "area_name": area.area_name,
                        "fixes": total_fixes,

                        "kwh_rate": kwh_rate,
                        "reading_month": reading_month,
                        "current_reading": f"{int(reading.current_reading):,}" if reading and reading.current_reading is not None else None,
                        "previous_reading": f"{int(reading.previous_reading):,}" if reading and reading.previous_reading is not None else None,
                        "usage": f"{int(reading.usage):,}" if reading and reading.usage is not None else None,

                        "activation_fee": f"{activation_fee:,}",
                        "amperage": amperage,
                        "total": (f"{total:,}" if total is not None else "0"),

                        "dollar_rate": f"{rates.get('dollar_rate'):,}",
                        "unpaid_arrears_lbp": f"{int(meter_arrears.get('total_unpaid_lbp', 0)):,}",
                        "unpaid_arrears_usd": f"{round(meter_arrears.get('total_unpaid_usd', 0), 2):,}",
                    }
                else:
                    fixed_fee = int(package.fixed_fee) if package.fixed_fee else 0.0
                 
                    bd = bill.due_date
                    if bd.month > 1:
                        prev_month = bd.month - 1
                        prev_year = bd.year
                    else:
                        prev_month = 12
                        prev_year = bd.year - 1
                    reading_month = f"{prev_month:02d}/{prev_year}"
                    total = (int(bill.amount_due_lbp) if bill.amount_due_lbp else 0.0) - total_fixes

                    item = {
                        "package_type": "fixed",
                        "bill_id": bill.bill_id,
                        "bill_due_date": bill_due_date_str,
                        "bill_number": bill.bill_number,

                        "usd_value": f"{int(bill.amount_due_usd):,}" if bill.amount_due_usd is not None else "0",
                        "lbp_value": f"{int(bill.amount_due_lbp):,}" if bill.amount_due_lbp is not None else "0",

                        "customer_name": meter.customer_full_name,
                        "customer_phone_number": meter.customer_phone_number,
                        "area_name": area.area_name,
                        "fixes": f"{total_fixes:,}",
                        "reading_month": reading_month,

                        "fixed_fee": f"{fixed_fee:,}",
                        "amperage": amperage,
                        "total": (f"{total:,}" if total is not None else "0"),
                        "dollar_rate": f"{rates.get('dollar_rate'):,}",
                        "fixed_sub_hours": f"{int(rates.get('fixed_sub_hours')):,}",
                        "fixed_sub_rate": f"{int(rates.get('fixed_sub_rate')):,}",
                        "unpaid_arrears_lbp": f"{int(meter_arrears.get('total_unpaid_lbp', 0)):,}",
                        "unpaid_arrears_usd": f"{round(meter_arrears.get('total_unpaid_usd', 0), 2):,}",
                    }

                result.append(item)

            logger.info(f"Prepared {len(result)} flattened bills for due_date {due_date.isoformat()}")
            return result

        except (
            BillNotFoundError,
            RateNotFoundError
        ):
            raise

        except Exception as e:
            logger.error(f"Error fetching bills for billing date {billing_date}: {e}")
            raise


    async def get_statement(self, year: int, meter_id: str, session: AsyncSession):
        """
        Get comprehensive statement for a specific meter for the entire year.
        Returns package info, rates, readings, payments, and bill status for each month.
        """
        try:
            logger.info(f"Generating statement for meter {meter_id} for year {year}")
            
            # Get meter and package info
            meter_query = await session.execute(
                select(Meters, Packages, Areas)
                .join(Packages, Meters.package_id == Packages.package_id)
                .join(Areas, Meters.area_id == Areas.area_id)
                .where(Meters.meter_id == meter_id)
            )
            meter_data = meter_query.one_or_none()
            
            if not meter_data:
                logger.error(f"Meter {meter_id} not found")
                raise MeterNotFoundError()
            
            meter, package, area = meter_data
            
            # Determine KWH rate based on elevation
            kwh_rate_type = "coastal" if area.elevation < 700 else "mountain"
            
            # Get all bills for this meter in the given year
            bills_query = await session.execute(
                select(Bills, Rates)
                .join(Rates, Bills.rate_id == Rates.rate_id)
                .where(
                    and_(
                        Bills.meter_id == meter_id,
                        func.extract('year', Bills.due_date) == year
                    )
                )
                .order_by(Bills.due_date)
            )
            bills_data = bills_query.all()
            
            # Get all payments for this meter in the given year
            payments_query = await session.execute(
                select(Payments)
                .where(
                    and_(
                        Payments.meter_id == meter_id,
                        func.extract('year', Payments.payment_date) == year
                    )
                )
                .order_by(Payments.payment_date)
            )
            payments_data = payments_query.scalars().all()
            
            # Group payments by bill_id
            payments_by_bill = defaultdict(list)
            for payment in payments_data:
                if payment.bill_id:
                    payments_by_bill[payment.bill_id].append(payment)
            
            # Get readings for usage-based meters
            readings_data = []
            if meter.package_type == "usage":
                readings_query = await session.execute(
                    select(Readings)
                    .where(
                        and_(
                            Readings.meter_id == meter_id,
                            func.extract('year', Readings.reading_date) == year,
                            Readings.status == "verified"
                        )
                    )
                    .order_by(Readings.reading_date)
                )
                readings_data = readings_query.scalars().all()
            
            # Group readings by billing period (month)
            readings_by_period = {}
            for reading in readings_data:
                # Determine billing period based on reading date
                reading_month = reading.reading_date.month
                reading_year = reading.reading_date.year
                
                # Billing period: if reading is between 6th-31st, it belongs to that month
                # If reading is between 1st-5th, it belongs to previous month
                if reading.reading_date.day >= 6:
                    period_month = reading_month
                    period_year = reading_year
                else:
                    if reading_month == 1:
                        period_month = 12
                        period_year = reading_year - 1
                    else:
                        period_month = reading_month - 1
                        period_year = reading_year
                
                period_key = f"{period_year}-{period_month:02d}"
                readings_by_period[period_key] = reading
            
            # Get fixes for the year
            fixes_query = await session.execute(
                select(Fixes)
                .where(
                    and_(
                        Fixes.meter_id == meter_id,
                        func.extract('year', Fixes.fix_date) == year
                    )
                )
            )
            fixes_data = fixes_query.scalars().all()
            
            # Group fixes by month
            fixes_by_month = defaultdict(list)
            for fix in fixes_data:
                month_key = f"{fix.fix_date.year}-{fix.fix_date.month:02d}"
                fixes_by_month[month_key].append(fix)
            
            # Build statement data for each month
            statement_months = []
            
            for month in range(1, 13):
                month_key = f"{year}-{month:02d}"
                
                # Find bill for this month (due date would be next month, 1st)
                due_month = month + 1 if month < 12 else 1
                due_year = year if month < 12 else year + 1
                
                bill_data = None
                rates_data = None
                for bill, rates in bills_data:
                    if (bill.due_date.month == due_month and 
                        bill.due_date.year == due_year):
                        bill_data = bill
                        rates_data = rates
                        break
                
                # Get reading for this billing period
                reading_data = readings_by_period.get(month_key)
                
                # Get payments for this bill
                bill_payments = []
                total_paid_lbp = 0
                total_paid_usd = 0.0
                if bill_data:
                    bill_payments = payments_by_bill.get(bill_data.bill_id, [])
                    total_paid_lbp = sum(p.amount_lbp for p in bill_payments)
                    total_paid_usd = sum(p.amount_usd for p in bill_payments)
                
                # Get fixes for this month
                month_fixes = fixes_by_month.get(month_key, [])
                total_fixes_cost = sum(int(fix.cost) for fix in month_fixes)
                
                # Build month data
                month_data = {
                    "month": month,
                    "month_name": calendar.month_name[month],
                    "billing_period": month_key,
                    
                    # Package info
                    "package_type": meter.package_type,
                    "amperage": int(package.amperage) if package.amperage else None,
                    
                    # Bill info
                    "bill_exists": bill_data is not None,
                    "bill_id": str(bill_data.bill_id) if bill_data else None,
                    "bill_number": bill_data.bill_number if bill_data else None,
                    "due_date": bill_data.due_date.isoformat() if bill_data else None,
                    "status": bill_data.status if bill_data else "no_bill",
                    
                    # Amounts
                    "amount_due_lbp": int(bill_data.amount_due_lbp) if bill_data else 0,
                    "amount_due_usd": int(bill_data.amount_due_usd) if bill_data else 0.0,
                    "total_paid_lbp": int(total_paid_lbp),
                    "total_paid_usd": int(total_paid_usd),
                    "unpaid_lbp": int(bill_data.amount_due_lbp - bill_data.total_paid_lbp) if bill_data else 0,
                    "unpaid_usd": int(bill_data.amount_due_usd - bill_data.total_paid_usd) if bill_data else 0.0,
                    
                    # Rates (if bill exists)
                    "dollar_rate": int(rates_data.dollar_rate) if rates_data else None,
                    "kwh_rate": int(getattr(rates_data, f"{kwh_rate_type}_kwh_rate")) if rates_data else None,
                    "kwh_rate_type": kwh_rate_type,
                    
                    # Fixes
                    "fixes_count": len(month_fixes),
                    "fixes_cost": int(total_fixes_cost),
                    "fixes": [
                        {
                            "fix_id": str(fix.fix_id),
                            "description": fix.description,
                            "cost": int(fix.cost),
                            "fix_date": fix.fix_date.isoformat()
                        } for fix in month_fixes
                    ],
                    
                    # Payments
                    "payments_count": len(bill_payments),
                    "payments": [
                        {
                            "payment_id": str(payment.payment_id),
                            "amount_lbp": int(payment.amount_lbp),
                            "amount_usd": int(payment.amount_usd),
                            "payment_date": payment.payment_date.isoformat(),
                            "payment_method": payment.payment_method
                        } for payment in bill_payments
                    ]
                }
                
                # Add usage-specific data
                if meter.package_type == "usage":
                    month_data.update({
                        "activation_fee": int(package.activation_fee) if package.activation_fee else 0.0,
                        "reading_exists": reading_data is not None,
                        "current_reading": int(reading_data.current_reading) if reading_data else None,
                        "previous_reading": int(reading_data.previous_reading) if reading_data else None,
                        "usage": int(reading_data.usage) if reading_data else None,
                        "reading_date": reading_data.reading_date.isoformat() if reading_data else None,
                        "reading_sequence": reading_data.reading_sequence if reading_data else None,
                    })
                    
                    # Calculate usage cost breakdown
                    if reading_data and rates_data:
                        usage_cost = int(reading_data.usage) * int(getattr(rates_data, f"{kwh_rate_type}_kwh_rate"))
                        month_data["usage_cost"] = usage_cost
                    else:
                        month_data["usage_cost"] = 0.0
                else:
                    # Fixed package data
                    month_data.update({
                        "fixed_fee": int(package.fixed_fee) if package.fixed_fee else 0.0,
                        "usage": None,
                        "current_reading": None,
                        "previous_reading": None,
                        "activation_fee": 0.0,
                        "usage_cost": 0.0
                    })
                
                statement_months.append(month_data)
            
            # Calculate year totals
            total_billed_lbp = sum(m["amount_due_lbp"] for m in statement_months)
            total_billed_usd = sum(m["amount_due_usd"] for m in statement_months)
            total_paid_lbp = sum(m["total_paid_lbp"] for m in statement_months)
            total_paid_usd = sum(m["total_paid_usd"] for m in statement_months)
            total_unpaid_lbp = sum(m["unpaid_lbp"] for m in statement_months)
            total_unpaid_usd = sum(m["unpaid_usd"] for m in statement_months)
            total_fixes_cost = sum(m["fixes_cost"] for m in statement_months)
            
            # Build final response
            statement = {
                "year": year,
                "meter_info": {
                    "meter_id": str(meter.meter_id),
                    "customer_name": meter.customer_full_name,
                    "customer_phone": meter.customer_phone_number,
                    "address": meter.address,
                    "area_name": area.area_name,
                    "elevation": int(area.elevation) if area.elevation else None,
                    "package_type": meter.package_type,
                    "amperage": int(package.amperage) if package.amperage else None,
                    "status": meter.status
                },
                "year_summary": {
                    "total_bills": len([m for m in statement_months if m["bill_exists"]]),
                    "total_billed_lbp": total_billed_lbp,
                    "total_billed_usd": total_billed_usd,
                    "total_paid_lbp": total_paid_lbp,
                    "total_paid_usd": total_paid_usd,
                    "total_unpaid_lbp": total_unpaid_lbp,
                    "total_unpaid_usd": total_unpaid_usd,
                    "total_fixes_cost": total_fixes_cost,
                    "payment_completion_rate": (total_paid_lbp / total_billed_lbp * 100) if total_billed_lbp > 0 else 0
                },
                "months": statement_months
            }
            
            logger.info(f"Statement generated successfully for meter {meter_id}, year {year}")
            return statement
            
        except MeterNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error in get_statement for meter {meter_id}, year {year}: {e}")
            raise
