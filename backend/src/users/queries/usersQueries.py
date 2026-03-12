from globals.utils.logger import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.exc import IntegrityError

from db.postgres.tables.users import Users

from src.users.exceptions.exceptions import (
    UserNotFoundError,
    UsernameAlreadyExistsError,
    PhoneNumberAlreadyExistsError,
)
 

class UsersQueries:
    def __init__(self):
        logger.info("UsersQueries initialized successfully")
 

    async def get_user_by_id(self, user_role:str, session: AsyncSession, user_id: str):
        try:
            query = select(Users).where(Users.user_id == user_id)
            if user_role.lower() == "admin":
                query = query.where(Users.role == "user")
                
            result = await session.execute(query)
            user = result.scalar_one_or_none()
            if not user:
                logger.error(f"User with ID {user_id} not found.")
                raise UserNotFoundError()
            logger.info(f"User {user.username} fetched successfully by ID {user_id}.")
            return {
                "user_id": str(user.user_id),
                "username": user.username,
                "phone_number": user.phone_number,
                "role": user.role,
            }
        except Exception as e:
            logger.error(f"Error fetching user by ID {user_id}: {str(e)}")
            raise 


    async def create_user(self, session: AsyncSession, user_data: dict):
        try:
            new_user = Users(**user_data)
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            logger.info(f"User {new_user.username} created successfully.")
            return {
                "user_id": str(new_user.user_id),
                "username": new_user.username,
                "phone_number": new_user.phone_number,
                "role": new_user.role,
            }
        
        except IntegrityError as e:
            logger.error(f"Integrity error creating user: {str(e)}")
            error_message = str(e.orig)
            if "uq_users_username" in error_message:
                raise UsernameAlreadyExistsError()
            if "uq_users_phone_number" in error_message:
                raise PhoneNumberAlreadyExistsError()
            raise

        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise


    async def update_user(self, session: AsyncSession, user_id: str, update_data: dict):
        try:
            get_user_query = select(Users).where(Users.user_id == user_id)
            result = await session.execute(get_user_query)
            user = result.scalar_one_or_none()
            if not user:
                logger.error(f"User with ID {user_id} not found.")
                raise UserNotFoundError()

            for key, value in update_data.items():
                setattr(user, key, value)

            await session.commit()
            await session.refresh(user)
            logger.info(f"User {user.username} updated successfully.")
            return {
                "user_id": str(user.user_id),
                "username": user.username,
                "phone_number": user.phone_number,
                "role": user.role,
            }

        except IntegrityError as e:
            logger.error(f"Integrity error updating user: {str(e)}")
            error_message = str(e.orig)
            if "uq_users_username" in error_message:
                raise UsernameAlreadyExistsError()
            if "uq_users_phone_number" in error_message:
                raise PhoneNumberAlreadyExistsError()
            raise

        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            raise


    async def delete_user(self, session: AsyncSession, user_id: str):
        try:
            get_user_query = select(Users).where(Users.user_id == user_id)
            result = await session.execute(get_user_query)
            user = result.scalar_one_or_none()
            if not user:
                logger.error(f"User with ID {user_id} not found.")
                raise UserNotFoundError(user_id=user_id)

            await session.delete(user)
            await session.commit()
            logger.info(f"User {user.username} deleted successfully.")
            return user

        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            raise


    async def search_users(self, user_role: str, session: AsyncSession, query: str = None, role: str = None, page: int = 1, limit: int = 10):
        try:
            search_query = select(Users)
            filters = []
            
            if user_role.lower() == "admin":
                filters.append(Users.role=="user")

            if query:
                filters.append(Users.username.ilike(f"%{query}%"))
            if role:
                filters.append(Users.role == role)

            if filters:
                search_query = search_query.where(and_(*filters))


            offset = (page - 1) * limit
            total_count_query = select(func.count()).select_from(search_query)
            total_count = await session.execute(total_count_query)
            total_count = total_count.scalar()

            total_pages = (total_count + limit - 1) // limit
            has_next = page < total_pages
            has_previous = page > 1

            search_query = search_query.offset(offset).limit(limit)

            result = await session.execute(search_query)
            users = result.scalars().all()
            users_list = [
                {
                    "user_id": str(user.user_id),
                    "username": user.username,
                    "phone_number": user.phone_number,
                    "role": user.role,
                }
                for user in users
            ]
            return  {
                "users": users_list,
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
            logger.error(f"Error searching users: {str(e)}")
            raise


    async def delete_user_by_id(self, session: AsyncSession, user_id: str):
        try:
            get_user_query = select(Users).where(Users.user_id == user_id)
            result = await session.execute(get_user_query)
            user = result.scalar_one_or_none()
            if not user:
                logger.error(f"User with ID {user_id} not found.")
                raise UserNotFoundError(user_id=user_id)

            await session.delete(user)
            await session.commit()
            logger.info(f"User {user.username} deleted successfully.")
            return user

        except Exception as e:
            logger.error(f"Error deleting user by ID {user_id}: {str(e)}")
            raise

        