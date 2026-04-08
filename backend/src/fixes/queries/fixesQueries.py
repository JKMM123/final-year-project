from globals.utils.logger import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select, func, delete, or_, and_, outerjoin
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from typing import Dict, Any, List

from db.postgres.tables.fixes import Fixes
from db.postgres.tables.meters import Meters

from src.fixes.exceptions.exceptions import (
    FixNotFoundError,
    MeterNotFoundError,
    MeterInactiveError,
)


class FixesQueries:
    def __init__(self):
        logger.info("Fixes Queries initialized successfully.")

    async def create_fix(self, session: AsyncSession, fix_data: Dict[str, Any], user_id: UUID) -> Fixes:
        """Create a new fix record"""
        try:
            # Validate meter exists and is active
            meter_query = select(Meters).where(
                and_(
                    Meters.meter_id == fix_data['meter_id']
                )
            )
            meter_result = await session.execute(meter_query)
            meter = meter_result.scalar_one_or_none()
            
            if not meter:
                logger.error(f"Meter with ID {fix_data['meter_id']} not found.")
                raise MeterNotFoundError()

            if meter.status == 'inactive':
                logger.error(f"Meter with ID {fix_data['meter_id']} is inactive.")
                raise MeterInactiveError()

            # Create fix record
            new_fix = Fixes(
                meter_id=fix_data['meter_id'],
                fix_date=fix_data['fix_date'],
                description=fix_data['description'],
                cost=fix_data['cost'],
                created_by=user_id
            )
            
            session.add(new_fix)
            await session.commit()
            await session.refresh(new_fix)
            
            logger.info(f"Fix {new_fix.fix_id} created successfully for meter {fix_data['meter_id']}")
            return new_fix
            

        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating fix: {e}")
            raise e
        

    async def get_fix_by_id(self, session: AsyncSession, fix_id: UUID) -> Fixes:
        """Get a specific fix by ID with meter details"""
        try:
            query = (
                select(Fixes)
                .where(Fixes.fix_id == fix_id)
            )
            result = await session.execute(query)
            fix = result.scalar_one_or_none()
            
            if not fix:
                logger.error(f"Fix with ID {fix_id} not found.")
                raise FixNotFoundError()
            
            logger.info(f"Fix {fix_id} retrieved successfully.")
            return {
                "fix_id": str(fix.fix_id),
                "meter_id": str(fix.meter_id),
                "fix_date": str(fix.fix_date),
                "description": fix.description,
                "cost": float(fix.cost)
            }
            
        except Exception as e:
            logger.error(f"Error retrieving fix {fix_id}: {e}")
            raise e


    async def update_fix(self, session: AsyncSession, fix_id: UUID, fix_data: Dict[str, Any], user_id: UUID) -> Fixes:
        """Update an existing fix"""
        try:
            # Check if fix exists
            existing_fix = await self.get_fix_by_id(session, fix_id)
            
            # Update fix data
            update_data = {
                **fix_data,
                'updated_by': user_id
            }
            
            query = update(Fixes).where(Fixes.fix_id == fix_id).values(**update_data)
            result = await session.execute(query)
            
            if result.rowcount == 0:
                raise FixNotFoundError()
            
            await session.commit()
            
            # Return updated fix
            logger.info(f"Fix {fix_id} updated successfully.")
            return True
        
        except Exception as e:
            await session.rollback()
            logger.error(f"Error updating fix {fix_id}: {e}")
            raise e


    async def delete_fixes(self, session: AsyncSession, fix_ids: List[UUID]) -> bool:
        """Delete multiple fixes by IDs"""
        try:
            query = delete(Fixes).where(Fixes.fix_id.in_(fix_ids))
            result = await session.execute(query)
            
            if result.rowcount == 0:
                logger.error(f"No fixes found with IDs: {fix_ids}")
                raise FixNotFoundError()
            
            await session.commit()
            logger.info(f"Deleted {result.rowcount} fixes successfully.")
            return True

        except Exception as e:
            await session.rollback()
            logger.error(f"Error deleting fixes: {e}")
            raise e


    async def search_fixes(self, session: AsyncSession, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Search fixes with pagination and filters"""
        try:
            page = filters.get('page', 1)
            limit = filters.get('limit', 10)
            offset = (page - 1) * limit
            
            # Base query with joins
            base_query = (
                select(Fixes, Meters)
                .join(Meters, Fixes.meter_id == Meters.meter_id)
            )
            
            # Apply filters
            conditions = []
            
            if filters.get('query'):
                search_term = f"%{filters['query']}%"
                conditions.append(
                    or_(
                        Fixes.description.ilike(search_term),
                        Meters.customer_full_name.ilike(search_term)
                    )
                )

            if filters.get('fix_date'):
                month = filters['fix_date'].month
                year = filters['fix_date'].year
                conditions.append( and_(
                    func.extract("month", Fixes.fix_date) == month,
                    func.extract("year", Fixes.fix_date) == year)
                )
            
            # Apply conditions to queries
            if conditions:
                base_query = base_query.where(and_(*conditions))
            
            # Order by fix_date descending
            base_query = base_query.order_by(Fixes.fix_date.desc())

            # Execute main query with pagination
            result = await session.execute(base_query.offset(offset).limit(limit))
            fixes = result.all()
            
            # Count query
            total_count = select(func.count()).select_from(base_query.subquery())
            total_result = await session.execute(total_count)
            total_count = total_result.scalar() or 0

            total_pages = (total_count + limit - 1) // limit
            has_next = page < total_pages
            has_previous = page > 1

            fixes_list = [
                {
                    "fix_id": str(fix.fix_id),
                    "meter_id": str(fix.meter_id),
                    "customer_name": meter.customer_full_name,
                    "description": fix.description,
                    "fix_date": fix.fix_date.isoformat(),
                    "cost": fix.cost,
                }
                for fix, meter in fixes
            ]
            
            logger.info(f"Found {len(fixes)} fixes (page {page}/{total_pages})")
            
            return {
                "fixes": fixes_list,
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
            logger.error(f"Error searching fixes: {e}")
            raise e

