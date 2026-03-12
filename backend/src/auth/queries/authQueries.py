from globals.utils.logger import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, update

from db.postgres.tables.users import Users
from db.postgres.tables.otp import OTP
from db.postgres.tables.refresh_tokens import RefreshTokens

from concurrent.futures import ThreadPoolExecutor
import asyncio

from globals.utils.hashingHelper import HashingHelper

from src.auth.exceptions.exceptions import (
    UsernameOrPhoneNotFoundError,
    InvalidPasswordError,
    OTPAlreadyExistsError,
    InvalidResetTokenError
)

from globals.exceptions.global_exceptions import UnauthorizedError

from src.auth.services.jwtService import JWTService

class AuthQueries:
    def __init__(self):
        logger.info("AuthQueries initialized successfully")


    async def insert_refresh_token(self, session: AsyncSession, user_id: str, token: str, device_id: str):
        try:
            # Check if a refresh token already exists for this user and device
            existing_token_query = (                
                select(RefreshTokens)
                .where(
                    and_(
                        RefreshTokens.user_id == user_id,
                        RefreshTokens.device_id == device_id,
                        RefreshTokens.revoked == False
                    )
                )
            )
            existing_token_result = await session.execute(existing_token_query)
            existing_token = existing_token_result.scalar_one_or_none()
            if existing_token:
                revoke_token_query = (
                    update(RefreshTokens)
                    .where(RefreshTokens.token_id == existing_token.token_id)
                    .values(revoked=True)
                )
                revoked_token_result = await session.execute(revoke_token_query)
                if revoked_token_result.rowcount == 0:
                    logger.error(f"Failed to revoke existing token for user_id: {user_id}")
                    raise Exception("Failed to revoke existing token")

            token_hash = await asyncio.to_thread(HashingHelper.generate_hash, token)

            new_refresh_token = RefreshTokens(
                user_id=user_id,
                token_hash=token_hash,
                device_id=device_id
            )

            session.add(new_refresh_token)
            await session.commit()
            logger.info(f"Refresh token inserted for user_id: {user_id}")
            return new_refresh_token
        
        except Exception as e:
            logger.error(f"Error inserting refresh token: {str(e)}")
            await session.rollback()
            raise


    async def login_query(self, username_or_phone: str, password: str, device_id: str,session: AsyncSession):
        try:
            get_user_query = (
                select(Users)
                .where(
                    or_(
                        Users.username == username_or_phone,
                        Users.phone_number == username_or_phone
                    )
                )
            )
            get_user_query_result = await session.execute(get_user_query)
            user = get_user_query_result.scalar_one_or_none()
            if not user:
                logger.error(f"User not found for username/phone: {username_or_phone}")
                raise UsernameOrPhoneNotFoundError()

            valid = await asyncio.to_thread(HashingHelper.verify_hash, password, user.password_hash)

            if not valid:
                logger.error(f"Invalid password for user: {username_or_phone}")
                raise InvalidPasswordError()
            
            logger.info(f"User {user.username} logged in successfully")

            # Generate JWT token
            new_access_token = JWTService.create_access_token(
                data={
                    "user_id": str(user.user_id),
                    "username": user.username,
                    "phone_number": user.phone_number,
                    "role": user.role,
                    "device_id": str(device_id)
                }
            )

            new_refresh_token = JWTService.create_refresh_token(
                data={
                    "user_id": str(user.user_id),
                    "device_id": str(device_id),
                    "username": user.username,
                    "phone_number": user.phone_number,
                    "role": user.role
                }
            )
            await self.insert_refresh_token(
                session=session,
                user_id=str(user.user_id),
                token=new_refresh_token,
                device_id=str(device_id)
            )
            return {
                "user_info": {
                    "user_id": str(user.user_id),
                    "username": user.username,
                    "phone_number": user.phone_number,
                    "role": user.role,
                },
                "tokens": {
                    "access_token": new_access_token,
                    "refresh_token": new_refresh_token
                }
            }

        except Exception as e:
            logger.error(f"Error in login_query: {str(e)}")
            raise 


    async def logout_query(self, session: AsyncSession, user_id: str, device_id: str):
        try:
            # Revoke the refresh token for the user and device
            revoke_token_query = (
                update(RefreshTokens)
                .where(
                    and_(
                        RefreshTokens.user_id == user_id,
                        RefreshTokens.device_id == device_id,
                        RefreshTokens.revoked == False
                    )
                )
                .values(revoked=True)
            )
            revoked_token_result = await session.execute(revoke_token_query)
            if revoked_token_result.rowcount == 0:
                logger.error(f"No active refresh token found for user_id: {user_id} and device_id: {device_id}")
                raise Exception("No active refresh token found")
            
            await session.commit()
            logger.info(f"Refresh token revoked successfully for user_id: {user_id} and device_id: {device_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error in logout_query: {str(e)}")
            await session.rollback()
            raise


    async def refresh_query(self, session: AsyncSession, user_id: str, device_id: str, decoded_jwt: dict):
        try:
            # Fetch the latest refresh token for the user and device
            get_refresh_token_query = (
                select(RefreshTokens)
                .where(
                    and_(
                        RefreshTokens.user_id == user_id,
                        RefreshTokens.device_id == device_id,
                        RefreshTokens.revoked == False
                    )
                )
            )
            get_refresh_token_result = await session.execute(get_refresh_token_query)
            refresh_token = get_refresh_token_result.scalar_one_or_none()
            if not refresh_token:
                logger.error(f"No active refresh token found for user_id: {user_id} and device_id: {device_id}")
                raise UnauthorizedError(
                    message="No active refresh token found. Please log in again."
                )
            

            # Verify the refresh token hash
            if not HashingHelper.verify_hash(decoded_jwt.get("refresh_token"), refresh_token.token_hash):
                logger.error("Invalid refresh token hash.")
                raise UnauthorizedError(
                    message="Invalid refresh token hash."
                )

            # Generate new access token
            new_access_token = JWTService.create_access_token(
                data={
                    "user_id": str(user_id),
                    "username": decoded_jwt.get("username"),
                    "phone_number": decoded_jwt.get("phone_number"),
                    "role": decoded_jwt.get("role"),
                    "device_id": str(device_id)
                }
            )
            return new_access_token
            
        except Exception as e:
            logger.error(f"Error in refresh_query: {str(e)}")
            raise

    
    async def get_user_by_phone(self, session: AsyncSession, phone_number: str):
        try:
            query = select(Users).where(Users.phone_number == phone_number)
            result = await session.execute(query)
            user = result.scalar_one_or_none()
            if not user:
                logger.error(f"User with phone number {phone_number} not found.")
                raise UsernameOrPhoneNotFoundError()
            logger.info(f'user with number {phone_number} exists')
            return user
        
        except Exception as e:
            logger.error(f"Error getting user by phone number {phone_number}: {e}")
            raise


    async def reset_password_query(self, session: AsyncSession, phone_number: str, new_password: str):
        try:
            # Hash the new password
            hashed_password = await asyncio.to_thread(HashingHelper.generate_hash, new_password)

            # Update the user's password
            update_password_query = (
                update(Users)
                .where(Users.phone_number == phone_number)
                .values(password_hash=hashed_password)
            )
            result = await session.execute(update_password_query)
            if result.rowcount == 0:
                logger.error(f"Failed to update password for phone_number: {phone_number}")
                raise Exception("Failed to update password")

            await session.commit()
            logger.info(f"Password updated successfully for phone_number: {phone_number}")
            return True
        
        except Exception as e:
            logger.error(f"Error in reset_password_query: {str(e)}")
            await session.rollback()
            raise



