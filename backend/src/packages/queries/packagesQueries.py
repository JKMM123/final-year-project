from globals.utils.logger import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select, func
from sqlalchemy.exc import IntegrityError

from db.postgres.tables.packages import Packages
from db.postgres.tables.meters import Meters

from src.packages.exceptions.exceptions import (
    PackagesNotFoundError,
    PackageAlreadyExistsError,
    PackageInUseError
)


class PackagesQueries:
    def __init__(self):
        logger.info("Packages Queries initialized successfully.")


    async def get_package_by_id(self, session: AsyncSession, package_id: str):
        try:
            query = select(Packages).where(Packages.package_id == package_id)
            result = await session.execute(query)
            pkg = result.scalar_one_or_none()
            if not pkg:
                logger.error(f"Package with ID {package_id} not found.")
                raise PackagesNotFoundError(amperage=None)
            
            logger.info(f"Package {pkg.package_id} fetched successfully.")
            return {
                "package_id": str(pkg.package_id),
                "amperage": pkg.amperage,
                "activation_fee": pkg.activation_fee,
                "fixed_fee": pkg.fixed_fee,
            }
        
        except Exception as e:
            logger.error(f"Error getting package by ID {package_id}: {e}")
            raise 


    async def create_package(self, session: AsyncSession, package_data: dict):
        try:
            new_pkg = Packages(**package_data)
            session.add(new_pkg)
            await session.commit()
            await session.refresh(new_pkg)
            logger.info(f"Package {new_pkg.package_id} created successfully.")
            return {
                "package_id": str(new_pkg.package_id),
                "amperage": new_pkg.amperage,
                "activation_fee": new_pkg.activation_fee,
                "fixed_fee": new_pkg.fixed_fee,
            }
        
        except IntegrityError as e:
            logger.error(f"Integrity error creating package: {e}")
            error_message = str(e.orig)
            if "uq_amperage" in error_message:
                raise PackageAlreadyExistsError(amperage=package_data.get('amperage'))
            raise

        except Exception as e:
            logger.error(f"Error creating package: {e}")
            raise 


    async def update_package(self, session: AsyncSession, package_id: str, update_data: dict):
        try:
            # fetch existing
            query = select(Packages).where(Packages.package_id == package_id)
            result = await session.execute(query)
            pkg = result.scalar_one_or_none()
            if not pkg:
                logger.error(f"Package with ID {package_id} not found.")
                raise PackagesNotFoundError()
            
            # apply updates
            for key, value in update_data.items():
                if value is not None:
                    setattr(pkg, key, value)

            await session.commit()
            await session.refresh(pkg)
            logger.info(f"Package {pkg.package_id} updated successfully.")
            return {
                "package_id": str(pkg.package_id),
                "amperage": pkg.amperage,
                "activation_fee": pkg.activation_fee,
                "fixed_fee": pkg.fixed_fee,
            }
        except IntegrityError as e:
            logger.error(f"Integrity error updating package: {e}")
            if "uq_amperage" in str(e.orig):
                logger.error(f"Package with amperage {update_data.get('amperage')} already exists.")
                raise PackageAlreadyExistsError(amperage=update_data.get('amperage'))
            
            raise
        
        except Exception as e:
            logger.error(f"Error updating package: {e}")
            raise 


    async def delete_package(self, session: AsyncSession, package_id: str):
        try:
            # fetch existing
            query = select(Packages).where(Packages.package_id == package_id)
            result = await session.execute(query)
            pkg = result.scalar_one_or_none()
            if not pkg:
                logger.error(f"Package with ID {package_id} not found.")
                raise PackagesNotFoundError()
            
            # check if package is in use
            in_use_query = select(func.count(Meters.meter_id)).where(Meters.package_id == pkg.package_id)
            in_use_count = await session.execute(in_use_query)
            in_use_count = in_use_count.scalar() 

            if in_use_count > 0:
                logger.error(f"Package {package_id} is in use and cannot be deleted.")
                raise PackageInUseError(amperage=pkg.amperage)

            await session.delete(pkg)
            await session.commit()
            logger.info(f"Package {package_id} deleted successfully.")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting package: {e}")
            raise


    async def search_packages(self, session: AsyncSession, amperage: int = None, page: int = 1, limit: int = 10):
        try:
            query = (
                select(Packages, func.count(Meters.package_id).label('total_count'))
                .join(Meters, Meters.package_id == Packages.package_id, isouter=True)
                .group_by(Packages.package_id)
            )
            if amperage is not None:
                query = query.where(Packages.amperage == amperage)
            # pagination
            total_q = select(func.count()).select_from(query.subquery())
            total = await session.execute(total_q)
            total = total.scalar() or 0
            offset = (page - 1) * limit
            result = await session.execute(query.offset(offset).limit(limit))
            rows = result.all()
            items = [
                {
                    "package_id": str(p.package_id),
                    "amperage": p.amperage,
                    "activation_fee": p.activation_fee,
                    "fixed_fee": p.fixed_fee,
                    "meters_count": total_count if total_count is not None else 0
                }
                for p, total_count in rows
            ]
            total_pages = (total + limit - 1) // limit
            return {
                "packages": items,
                "pagination": {
                    "current_page": page,
                    "per_page": limit,
                    "total_items": total,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_previous": page > 1,
                }
            }
        except Exception as e:
            logger.error(f"Error searching packages: {e}")
            raise


