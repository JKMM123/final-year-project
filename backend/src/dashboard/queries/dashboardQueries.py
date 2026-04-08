from globals.utils.logger import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select, func, delete, or_, and_, text, extract, cast, Integer
from db.postgres.tables.bills import Bills
from db.postgres.tables.readings import Readings
from db.postgres.tables.packages import Packages
from db.postgres.tables.payments import Payments
from db.postgres.tables.meters import Meters
from db.postgres.tables.rates import Rates
from db.postgres.tables.areas import Areas
from datetime import datetime, timezone
import asyncio


class DashboardQueries:
    def __init__(self):
        logger.info("Dashboard Queries initialized successfully.")


    async def get_dashboard_summary(self, session: AsyncSession, month: str):
        """
        Get dashboard summary metrics for the given month (yyyy-mm format)
        Uses asyncio to run queries in parallel for optimization
        """
        try:
            # Parse month to get year and month integers
            year, month_num = map(int, month.split('-'))

            # Run all queries sequentially instead of using asyncio.gather
            meter_counts = await self._get_meter_status_counts(session)
            reading_counts = await self._get_readings_status_counts(session, year, month_num)
            meters_without_readings = await self._get_meters_without_readings_count(session, year, month_num)
            bill_counts = await self._get_bills_status_counts(session, year, month_num)
            month_bill_ids = await self._get_month_bills(session, year, month_num)
            bill_payment_status_counts = await self._get_bills_payment_status_counts(session, month_bill_ids)
            earnings = await self._get_total_earnings_by_payment_method(session, month_bill_ids)
            unpaid_arrears = await self.get_total_unpaid_arrears(session, month_bill_ids)

            return {
                "month": month,
                "meters": meter_counts,
                "readings": reading_counts,
                "meters_without_readings": meters_without_readings,
                "bills": bill_counts,
                "bills_payment_status": bill_payment_status_counts,
                "earnings": earnings,
                "unpaid_arrears": unpaid_arrears
            }
            
        except Exception as e:
            logger.error(f"Error in get_dashboard_summary: {e}")
            raise


    async def _get_meter_status_counts(self, session: AsyncSession):
        """Get count of active/inactive meters"""
        try:
            query = select(
                Meters.status,
                Meters.package_type,
                func.count(Meters.meter_id).label('count')
            ).group_by(Meters.status, Meters.package_type)
            
            result = await session.execute(query)
            rows = result.all()
            
            # Initialize nested structure
            counts = {
                "active": {"fixed": 0, "usage": 0, "total": 0},
                "inactive": {"fixed": 0, "usage": 0, "total": 0},
                "total": {"fixed": 0, "usage": 0, "total": 0}
            }
            
            # Process results
            for row in rows:
                status = row.status
                package_type = row.package_type
                count = row.count
                
                if status in counts and package_type in ["fixed", "usage"]:
                    counts[status][package_type] = count
                    counts[status]["total"] += count
                    counts["total"][package_type] += count
                    counts["total"]["total"] += count
                
            return counts
            
        except Exception as e:
            logger.error(f"Error getting meter status counts: {e}")
            raise


    async def _get_readings_status_counts(self, session: AsyncSession, year: int, month: int):
        """Get count of verified/unverified readings for given month"""
        try:
            query = select(
                Readings.status,
                func.count(Readings.reading_id).label('count')
            ).where(
                and_(
                    cast(extract('year', Readings.reading_date), Integer) == year,
                    cast(extract('month', Readings.reading_date), Integer) == month
                )
            ).group_by(Readings.status)
            
            result = await session.execute(query)
            rows = result.all()
            
            counts = {"verified": 0, "pending": 0}
            for row in rows:
                if row.status in counts:
                    counts[row.status] = row.count
                    
            return counts
            
        except Exception as e:
            logger.error(f"Error getting readings status counts: {e}")
            raise


    async def _get_meters_without_readings_count(self, session: AsyncSession, year: int, month: int):
        """Get count of meters that don't have readings for the given month"""
        try:
            # Subquery to get meters that have readings in the given month
            readings_subquery = select(Readings.meter_id.distinct()).where(
                and_(
                    cast(extract('year', Readings.reading_date), Integer) == year,
                    cast(extract('month', Readings.reading_date), Integer) == month
                )
            )
            
            # Count meters that are NOT in the readings subquery
            query = select(func.count(Meters.meter_id)).where(
                Meters.meter_id.notin_(readings_subquery),
                Meters.status == "active",
                Meters.package_type == 'usage'
            )
            
            result = await session.execute(query)
            count = result.scalar() or 0
            
            return count
            
        except Exception as e:
            logger.error(f"Error getting meters without readings count: {e}")
            raise


    async def _get_bills_status_counts(self, session: AsyncSession, year: int, month: int):
        """Get count of generated/ungenerated bills for given month"""
        try:
            # Get total meters count
            total_meters_query = select(func.count(Meters.meter_id))
            total_meters_result = await session.execute(total_meters_query)
            total_meters = total_meters_result.scalar() or 0

            year=year if month < 12 else year + 1
            month=month + 1 if month < 12 else 1
            
            # Get generated bills count for the month
            generated_bills_query = select(func.count(Bills.bill_id)).where(
                and_(
                    cast(extract('year', Bills.due_date), Integer) == year,
                    cast(extract('month', Bills.due_date), Integer) == month
                )
            )
            
            generated_result = await session.execute(generated_bills_query)
            generated_bills = generated_result.scalar() or 0
            
            return {
                "generated": generated_bills,
                "ungenerated": max(0, total_meters - generated_bills)
            }
            
        except Exception as e:
            logger.error(f"Error getting bills status counts: {e}")
            raise


    async def _get_total_earnings_by_payment_method(self, session: AsyncSession, month_bill_ids: list):
        """Get total earnings for the month grouped by payment method"""
        try:
            query = (
                select(
                    Payments.payment_method,
                    func.sum(Payments.amount_lbp).label('total_earnings_lbp'),
                    func.sum(Payments.amount_usd).label('total_earnings_usd')
                    )
                .where(
                    Payments.bill_id.in_(month_bill_ids)
                )
                .group_by(Payments.payment_method)
            )

            result = await session.execute(query)
            rows = result.all()
            
            earnings = {}
            total_earnings_lbp = 0
            total_earnings_usd = 0
            for row in rows:
                if row.payment_method:
                    earnings[row.payment_method] = {
                        "total_earnings_lbp": float(row.total_earnings_lbp or 0),
                        "total_earnings_usd": float(row.total_earnings_usd or 0)
                    }
                    total_earnings_lbp += float(row.total_earnings_lbp or 0)
                    total_earnings_usd += float(row.total_earnings_usd or 0)
    
            
            earnings["total"] = {
                "total_earnings_lbp": total_earnings_lbp,
                "total_earnings_usd": total_earnings_usd
            }
            
            return earnings
            
        except Exception as e:
            logger.error(f"Error getting total earnings by payment method: {e}")
            raise


    async def _get_bills_payment_status_counts(self, session: AsyncSession, month_bill_ids: list):
        """Get count of paid/unpaid bills for given month with payment method breakdown"""
        try:

            # Get total counts by status
            status_query = select(
                Bills.status,
                func.count(Bills.bill_id).label('count')
            ).where(
                Bills.bill_id.in_(month_bill_ids)
            ).group_by(Bills.status)
            
            # Get payment method breakdown for paid bills
            payment_method_query = (
                select(
                    Payments.payment_method,
                    func.count(Payments.bill_id).label('count')
            )
            .join(Bills, Payments.bill_id == Bills.bill_id)
            .where(
                and_(
                    Bills.status == 'paid',
                    Bills.bill_id.in_(month_bill_ids)
                )
            )
            .group_by(Payments.payment_method)
            )
            
            # Execute both queries
            status_result = await session.execute(status_query)
            status_rows = status_result.all()

            payment_method_result = await session.execute(payment_method_query)
            payment_method_rows = payment_method_result.all()
            
            # Build status counts
            counts = {"paid": {"total": 0}, "unpaid": 0, "partially_paid": 0}
            
            for row in status_rows:
                if row.status == "paid":
                    counts["paid"]["total"] = row.count
                elif row.status == "unpaid":
                    counts["unpaid"] = row.count
                elif row.status == "partially_paid":
                    counts["partially_paid"] = row.count
            
            # Add payment method breakdown for paid bills
            for row in payment_method_rows:
                if row.payment_method:
                    counts["paid"][row.payment_method] = row.count
                    
            return counts
            
        except Exception as e:
            logger.error(f"Error getting bills payment status counts: {e}")
            raise


    async def _get_month_bills(self, session: AsyncSession, year: int, month: int):
        """Helper to get bill IDs for the given month"""
        try:
            year=year if month < 12 else year + 1
            month=month + 1 if month < 12 else 1

            query = select(Bills.bill_id).where(
                and_(
                    cast(extract('year', Bills.due_date), Integer) == year,
                    cast(extract('month', Bills.due_date), Integer) == month
                )
            )
            result = await session.execute(query)
            bill_ids = [row.bill_id for row in result.all()]
            return bill_ids
            
        except Exception as e:
            logger.error(f"Error getting month bills: {e}")
            raise


    async def get_total_unpaid_arrears(self, session: AsyncSession, month_bill_ids: list):
        """Get total unpaid arrears across all meters"""
        try:
            # Sum of unpaid arrears in LBP and USD
            total_unpaid = (
                select(
                    func.sum(Bills.amount_due_lbp - Bills.total_paid_lbp).label('total_unpaid_lbp'),
                    func.sum(Bills.amount_due_usd - Bills.total_paid_usd).label('total_unpaid_usd')
                )
            .where(
                Bills.status.in_(['unpaid', 'partially_paid'])
                )
            )

            total_unpaid_this_month = (
                select(
                    func.sum(Bills.amount_due_lbp - Bills.total_paid_lbp).label('total_unpaid_lbp'),
                    func.sum(Bills.amount_due_usd - Bills.total_paid_usd).label('total_unpaid_usd')
                )
            .where(
                and_(
                    Bills.bill_id.in_(month_bill_ids),
                    Bills.status.in_(['unpaid', 'partially_paid'])
                    )   
                )
            )
            # Execute both queries
            total_unpaid_result = await session.execute(total_unpaid)
            total_unpaid_this_month_result = await session.execute(total_unpaid_this_month)

            total_unpaid_row = total_unpaid_result.first()
            total_unpaid_this_month_row = total_unpaid_this_month_result.first()

            return {
                "total_unpaid_lbp": int(total_unpaid_row.total_unpaid_lbp or 0) if total_unpaid_row else 0,
                "total_unpaid_usd": float(total_unpaid_row.total_unpaid_usd or 0) if total_unpaid_row else 0.0,
                "total_unpaid_this_month_lbp": int(total_unpaid_this_month_row.total_unpaid_lbp or 0) if total_unpaid_this_month_row else 0,
                "total_unpaid_this_month_usd": float(total_unpaid_this_month_row.total_unpaid_usd or 0) if total_unpaid_this_month_row else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error getting total unpaid arrears: {e}")
            raise

