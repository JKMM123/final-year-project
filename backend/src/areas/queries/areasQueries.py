from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, and_, delete
from globals.utils.logger import logger
from sqlalchemy.exc import IntegrityError, NoResultFound

from db.postgres.tables.meters import Meters
from db.postgres.tables.areas import Areas

from src.areas.exceptions.exceptions import (
    AreaAlreadyExistsException,
    AreaLinkedToMetersException,
    AreaNotFoundException
)

class AreasQueries:
    def __init__(self):
        logger.info("AreasQueries initialized successfully. ")


    async def create_area_query(
            self, 
            area_name: str, 
            elevation: int,
            created_by: str,
            session: AsyncSession
            ):
        """
        Create a query to insert a new area.
        """
        try:
            new_area = Areas(
                area_name=area_name.lower(),
                elevation=elevation,
                created_by=created_by,
                updated_by=created_by
            )
            session.add(new_area)
            await session.commit()
            logger.info(f"Area '{area_name}' created successfully.")
            new_area_data = {
                "area_id": str(new_area.area_id),
                "area_name": new_area.area_name,
                "elevation": new_area.elevation,
                "number_of_customers": 0
            }
            return new_area_data


        except IntegrityError as e:
            await session.rollback()
            error_messaqe = str(e.orig)
            if "unique constraint" in error_messaqe.lower():
                if "uq_area_name" in error_messaqe.lower():
                    logger.error(f"Area with name '{area_name}' already exists for this business.")
                    raise AreaAlreadyExistsException(area_name=area_name)
                
            logger.error(f"Integrity error while creating area: {e}")
            raise e



        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating area: {e}")
            raise e


    async def delete_area_query(
            self, 
            area_id: str, 
            session: AsyncSession
            ):
        """
        Delete an area by ID.
        """
        try:
            nbr_of_meters_assigned_to_area = (
                select(func.count(Meters.meter_id))
                .where(
                    and_(
                        Meters.area_id == area_id,
                    )
                )
            )
            result = await session.execute(nbr_of_meters_assigned_to_area)
            meters_count = result.scalar_one()
            if meters_count > 0:
                logger.error(f"Cannot delete area '{area_id}' as it has {meters_count} meters assigned.")
                raise AreaLinkedToMetersException(number_of_meters=meters_count)

            delete_query = delete(Areas).where(
                and_(
                    Areas.area_id == area_id
                )
            )
            result = await session.execute(delete_query)
            await session.commit()
            if result.rowcount == 0:
                logger.error(f"Area with ID '{area_id}' not found.")
                raise AreaNotFoundException()
            logger.info(f"Area with ID '{area_id}' deleted successfully.")

            return True
        
        except (
            AreaNotFoundException,
            AreaLinkedToMetersException
        ):
            raise

        except Exception as e:
            await session.rollback()
            logger.error(f"Error deleting area: {e}")
            raise e
        

    async def search_areas_query(
            self, 
            search_query: str | None,
            page: int,
            limit: int,
            session: AsyncSession
            ):
        """
        Search for areas by business ID and optional area name.
        """
        try:
            offset = (page - 1) * limit
            query = (
                select(
                    Areas,
                    func.count(Meters.meter_id).label('meters_count')
                )
                .outerjoin(Meters, Areas.area_id == Meters.area_id)
            )
                
            if search_query:
                search_term = f"%{search_query}%"
                query = query.where(
                    or_(
                        Areas.area_name.ilike(search_term)
                    )
                )

            query = (
                query
                .group_by(Areas.area_id)
                .offset(offset)
                .limit(limit)
                .order_by(
                Areas.area_name.asc()
            ))
            results = await session.execute(query)
            areas = results.all()

            count_query = (
                select(func.count(Areas.area_id))
            )
            if search_query:  # Apply same filter to count query
                search_term = f"%{search_query}%"
                count_query = count_query.where(
                    or_(
                        Areas.area_name.ilike(search_term)
                    )
                )

            total_count_result = await session.execute(count_query)
            total_areas_count = total_count_result.scalar()

            total_pages = (total_areas_count + limit - 1) // limit
            has_next = page < total_pages
            has_previous = page > 1

            areas_list = [
                {
                    "area_id": str(area.area_id),
                    "area_name": area.area_name,
                    "elevation": area.elevation,
                    "number_of_meters": meters_count
                } for area, meters_count in areas
            ]
            logger.info(f"Found {len(areas_list)} areas.")
            return {
                "areas": areas_list,
                "pagination": {
                    "current_page": page,
                    "per_page": limit,
                    "total_items": total_areas_count,
                    "total_pages": total_pages,
                    "has_next": has_next,
                    "has_previous": has_previous,
                    "next_page": page + 1 if has_next else None,
                    "previous_page": page - 1 if has_previous else None
                }
            }
            

        except Exception as e:
            logger.error(f"Error searching areas: {e}")
            raise e
        

    async def update_area_query(
            self, 
            area_id: str, 
            elevation: int, 
            area_name: str, 
            updated_by: str,
            session: AsyncSession
            ):
        """
        Update an existing area.
        """
        try:
            update_query = (
                select(Areas)
                .where(
                        Areas.area_id == area_id,
                )
            )
            result = await session.execute(update_query)
            area = result.scalar_one()
            
            area.area_name = area_name.lower()  
            area.elevation = elevation
            area.updated_by = updated_by
            await session.commit()
            logger.info(f"Area '{area_name}' updated successfully.")

            nbr_of_meters_assigned_to_area = (
                select(func.count(Meters.meter_id))
                .where(
                    and_(
                        Meters.area_id == area_id,
                    )
                )
            )
            result = await session.execute(nbr_of_meters_assigned_to_area)
            meters_count = result.scalar_one()
            
            return {
                "area_id": str(area.area_id),
                "elevation": area.elevation,
                "area_name": area.area_name,
                "number_of_meters": meters_count
            }
        
        except NoResultFound:
            logger.error(f"Area with ID '{area_id}' not found.")
            raise AreaNotFoundException()
        
        except IntegrityError as e:
            await session.rollback()
            error_message = str(e.orig)
            if "unique constraint" in error_message.lower():
                if "uq_area_name" in error_message.lower():
                    logger.error(f"Area with name '{area_name}' already exists for this business.")
                    raise AreaAlreadyExistsException(area_name=area_name)
                
            logger.error(f"Integrity error while updating area: {e}")
            raise e

        except Exception as e:
            await session.rollback()
            logger.error(f"Error updating area: {e}")
            raise e

