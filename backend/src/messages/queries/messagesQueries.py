from globals.utils.logger import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select, func, delete, or_, and_
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone, date
from db.postgres.tables.templates import Templates
from db.postgres.tables.areas import Areas
from db.postgres.tables.packages import Packages
from db.postgres.tables.meters import Meters
from db.postgres.tables.bills import Bills
from db.postgres.tables.payments import Payments

from uuid import UUID
from datetime import datetime, date
from zoneinfo import ZoneInfo
from src.templates.exceptions.exceptions import (
    TemplateNotFoundError,
    TemplateAlreadyExistsError,
    InvalidAreasProvidedError,
    InvalidCustomersProvidedError,
    InvalidPackagesProvidedError,
)
 

class MessagesQueries:
    def __init__(self):
        self.timezone = ZoneInfo("Asia/Beirut")
        logger.info("Messages Queries initialized successfully.")


    async def validate_meter_filters(self, filters: dict, session: AsyncSession):
        try:
            validated_filters = {}
            if 'area_ids' in filters:
                # Check if all area IDs exist in database
                area_ids = filters['area_ids']
                stmt = select(Areas).where(Areas.area_id.in_([str(area_id) for area_id in area_ids]))
                result = await session.execute(stmt)
                existing_areas = {row.area_id for row in result.scalars().all()}
                missing_areas = [str(area_id) for area_id in area_ids if area_id not in existing_areas]
                
                if missing_areas:
                    logger.error(f"Invalid area IDs provided: {', '.join(missing_areas)}")
                    raise InvalidAreasProvidedError(missing_areas)
                logger.info(f"All provided area IDs are valid")
                validated_filters['area_ids'] = area_ids

            # Validate package_ids
            if 'package_ids' in filters and filters['package_ids'] is not None:
                package_ids = filters['package_ids']

                stmt = select(Packages).where(Packages.package_id.in_(package_ids))
                result = await session.execute(stmt)
                existing_packages = {row.package_id for row in result.scalars().all()}
                missing_packages = [str(package_id) for package_id in package_ids if package_id not in existing_packages]
                
                if missing_packages:
                    logger.error(f"Invalid package IDs provided: {', '.join(missing_packages)}")
                    raise InvalidPackagesProvidedError(missing_packages)
                logger.info(f"All provided package IDs are valid")
                validated_filters['package_ids'] = package_ids

            if "package_type" in filters:
                package_type = filters["package_type"]
                logger.info(f"All provided package types are valid")
                validated_filters['package_type'] = package_type

            if "meter_status" in filters:
                meter_status = filters["meter_status"]
                logger.info(f"All provided meter statuses are valid")
                validated_filters['meter_status'] = meter_status

            return validated_filters

        except Exception as e:
            logger.info(f"Error validating meter filters: {str(e)}")
            raise


    async def validate_bill_filters(self, filters: dict, session: AsyncSession):
        try:
            validated_filters = {}

            if "due_date" in filters:
                due_date = filters['due_date']
                year, month = map(int, due_date.split('-'))

                due_date = date(
                    year=year if month < 12 else year + 1,
                    month=month + 1 if month < 12 else 1,
                    day=1,
                )
                logger.info(f"due_date validated as {due_date}")
                validated_filters['due_date'] = due_date 

            if "payment_status" in filters:
                payment_status = filters['payment_status']
                logger.info(f"payment_status validated as {payment_status}")
                validated_filters['payment_status'] = payment_status

            if "payment_method" in filters:
                payment_method = filters['payment_method']
                logger.info(f"All provided payment methods are valid")
                validated_filters['payment_method'] = payment_method

            if "overdue_only" in filters:
                overdue_only = filters['overdue_only']
                logger.info(f"All provided overdue_only flags are valid")
                validated_filters['overdue_only'] = overdue_only

            return validated_filters

        except Exception as e:
            logger.info(f"Error validating bill filters: {str(e)}")
            raise


    async def check_template_exists(self, template_id:str, session: AsyncSession) -> bool:
        try:
            query = select(Templates).where(Templates.template_id == template_id)
            result = await session.execute(query)
            template = result.scalar_one_or_none()
            if not template:
                logger.error(f"Template with ID {template_id} does not exist.")
                raise TemplateNotFoundError()
            logger.info(f"Template with ID {template_id} found.")
            return {
                "name": template.name,
                "message": template.message,
            }

        except Exception as e:
            logger.info(f"Error checking template existence: {str(e)}")
            raise


    async def check_all_customers_exists(self, customer_ids: list[UUID], session: AsyncSession) -> bool:
        try:
            query = select(Meters).where(Meters.meter_id.in_(customer_ids))
            result = await session.execute(query)
            existing_customers = {row.meter_id for row in result.scalars().all()}
            missing_customers = {str(customer_id) for customer_id in customer_ids if customer_id not in existing_customers}

            if missing_customers:
                logger.error(f"Invalid customer IDs provided: {', '.join(missing_customers)}")
                raise InvalidCustomersProvidedError(missing_customers)
            logger.info(f"All provided customer IDs are valid")
            return True

        except Exception as e:
            logger.info(f"Error checking all customer existence: {str(e)}")
            raise


    async def get_customers_to_notify(self, data: dict, session: AsyncSession):
        try:
            filters = {}
            # check if template exists
            template_id = data.get("template_id", None)
            message = data.get("message", None)
            if template_id:
                template = await self.check_template_exists(template_id, session)

            # check if broadcast
            broadcast = data.get("broadcast", False)
            if broadcast:
                logger.info("Broadcast is True, fetching all customers.")
                filters["broadcast"] = True

            # check if specific customers provided
            customer_ids = data.get("customer_ids", [])
            if customer_ids:
                await self.check_all_customers_exists(customer_ids, session)
                filters["customer_ids"] = customer_ids

            meter_filters = data.get("meter_filters", {})
            if meter_filters:
                not_none_meter_filters = {k: v for k, v in meter_filters.items() if v is not None}
                validated_meter_filters = await self.validate_meter_filters(not_none_meter_filters, session)
                filters["meter_filters"] = validated_meter_filters

            bill_filters = data.get("bill_filters", {})
            if bill_filters:
                not_none_bill_filters = {k: v for k, v in bill_filters.items() if v is not None}
                validated_bill_filters = await self.validate_bill_filters(not_none_bill_filters, session)
                filters["bill_filters"] = validated_bill_filters

            customers_to_notify = await self.messages_query_builder(filters, session)   

            if template_id:
                return customers_to_notify, template.get('message')
            return customers_to_notify, message

        except Exception as e:
            logger.info(f"Error fetching customers to notify: {str(e)}")
            raise
            

    async def messages_query_builder(self, filters: dict, session: AsyncSession):
        try:
            # Base columns to select
            select_columns = [
                Meters.meter_id,
                Meters.customer_full_name,
                Meters.customer_phone_number,
                Meters.address
            ]
            
            # Track which JOINs we need based on filters
            joins_needed = set()
            
            # Check if we need area or package names
            meter_filters = filters.get("meter_filters", {})
            if meter_filters:
                if "area_ids" in meter_filters:
                    select_columns.append(Areas.area_name)
                    joins_needed.add('areas')
                    
                if "package_ids" in meter_filters:
                    select_columns.append(Packages.amperage)
                    select_columns.append(Packages.activation_fee)
                    select_columns.append(Packages.fixed_fee)
                    joins_needed.add('packages')

            bill_filters = filters.get("bill_filters", {})
            if bill_filters:
                select_columns.append(Bills.amount_due_lbp)  
                select_columns.append(Bills.amount_due_usd)  
                select_columns.append(Bills.due_date)  
                select_columns.append(Bills.blob_name)
                joins_needed.add('bills')


            # Build the base query
            query = select(*select_columns).select_from(Meters)
            
            # Add JOINs based on what's needed
            if 'areas' in joins_needed:
                query = query.join(Areas, Meters.area_id == Areas.area_id)
            if 'packages' in joins_needed:
                query = query.join(Packages, Meters.package_id == Packages.package_id)
            if 'bills' in joins_needed:
                query = query.join(Bills, Meters.meter_id == Bills.meter_id)

            # Handle broadcast scenario
            if filters.get("broadcast"):
                query = query.where(Meters.status == "active")
                
            # Handle specific customer IDs
            elif filters.get("customer_ids"):
                customer_ids = filters["customer_ids"]
                query = query.where(Meters.meter_id.in_(customer_ids))
                
            # Handle filtered scenarios
            else:
                conditions = []
                
                # Apply meter filters
                if meter_filters:
                    
                    # Area filter
                    if "area_ids" in meter_filters:
                        area_ids = [str(aid) for aid in meter_filters["area_ids"]]
                        conditions.append(Meters.area_id.in_(area_ids))
                        
                    # Package filter
                    if "package_ids" in meter_filters:
                        package_ids = [str(pid) for pid in meter_filters["package_ids"]]
                        conditions.append(Meters.package_id.in_(package_ids))
                        
                    # Package type filter
                    if "package_type" in meter_filters:
                        package_type = meter_filters["package_type"]
                        if package_type != "all":
                            conditions.append(Meters.package_type == package_type)
                            
                    # Meter status filter
                    if "meter_status" in meter_filters:
                        meter_status = meter_filters["meter_status"]
                        if meter_status != "all":
                            conditions.append(Meters.status == meter_status)
                
                # Apply bill filters (requires subquery)
                bill_filters = filters.get("bill_filters", {})
                if bill_filters:
                    # Create subquery to get meter_ids that match bill criteria
                    bill_subquery = select(Bills.meter_id).distinct().where(Bills.due_date == bill_filters['due_date'])
                    bill_conditions = []
                    
                    # Payment status filter
                    if "payment_status" in bill_filters:
                        payment_status = bill_filters["payment_status"]
                        if payment_status == "paid":
                            bill_conditions.append(Bills.status == "paid")
                        elif payment_status == "unpaid":
                            bill_conditions.append(Bills.status == "unpaid")
                        elif payment_status == "partially_paid":
                            bill_conditions.append(Bills.status == "partially_paid")
                        # "all" means no filter
                    
                    # Overdue filter
                    if "overdue_only" in bill_filters and bill_filters["overdue_only"]:
                        today = datetime.now(self.timezone).date()
                        current_month_10th = date(today.year, today.month, 10)
                        
                        # If we're past the 10th of current month, also include previous month's 10th
                        if today.day >= 10:
                            overdue_deadline = current_month_10th
                        else:
                            if today.month == 1:
                                overdue_deadline = date(today.year - 1, 12, 10)
                            else:
                                overdue_deadline = date(today.year, today.month - 1, 10)
                        logger.info(f"Overdue deadline calculated as: {overdue_deadline}")
                        bill_conditions.append(and_(
                            Bills.due_date <= overdue_deadline,
                            Bills.status == "unpaid"
                        ))
                    
                    # Payment method filter
                    if "payment_method" in bill_filters:
                        payment_methods = bill_filters["payment_method"]
                        if "all" not in payment_methods:
                            # Join with Payments table
                            bill_subquery = bill_subquery.join(
                                Payments,
                                Bills.bill_id == Payments.bill_id
                            )
                            bill_conditions.append(Payments.payment_method.in_(payment_methods))
                    
                    # Apply bill conditions to subquery
                    if bill_conditions:
                        bill_subquery = bill_subquery.where(and_(*bill_conditions))
                    
                    # Add meter filter: must have bills matching criteria
                    conditions.append(Meters.meter_id.in_(bill_subquery))
                
                # Apply all conditions to main query
                if conditions:
                    query = query.where(and_(*conditions))
            
            # Execute query
            result = await session.execute(query)
            customers = []
            
            for row in result:
                customer = {
                    "meter_id": str(row.meter_id),
                    "customer_full_name": row.customer_full_name,
                    "customer_phone_number": row.customer_phone_number,
                    "address": row.address
                }
                
                # Add area name if areas were joined
                if hasattr(row, 'area_name'):
                    customer["area_name"] = row.area_name

                # Add package details if packages were joined
                if hasattr(row, 'amperage'):
                    customer["amperage"] = row.amperage
                if hasattr(row, 'fixed_fee'):
                    customer["fixed_fee"] = row.fixed_fee
                if hasattr(row, 'activation_fee'):
                    customer["activation_fee"] = row.activation_fee

                # Add bill details
                if hasattr(row, 'amount_due_lbp'):
                    customer["amount_due_lbp"] = row.amount_due_lbp
                if hasattr(row, 'amount_due_usd'):
                    customer["amount_due_usd"] = row.amount_due_usd
                if hasattr(row, 'due_date'):
                    customer["due_date"] = row.due_date.isoformat()
                if hasattr(row, 'blob_name'):
                    customer["blob_name"] = row.blob_name

                customers.append(customer)
            
            logger.info(f"Query built successfully, found {len(customers)} customers")
            return customers

        except Exception as e:
            logger.error(f"Error building messages query: {str(e)}")
            raise




