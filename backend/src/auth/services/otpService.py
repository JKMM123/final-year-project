from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.postgres.tables.otp import OTP
from db.postgres.tables.passwordReset import PasswordReset
from datetime import datetime, timezone, timedelta
from globals.utils.logger import logger
import random
import secrets
import httpx
import asyncio

from src.auth.exceptions.exceptions import (
    OTPAlreadyExistsError,
    OTPInvalidError,
    InvalidResetTokenError,
    ErrorSendingOTP
)


class OTPService:

    @staticmethod
    async def check_otp_exists(session: AsyncSession, phone_number: str):
        try:
            query = select(OTP).where(OTP.phone_number == phone_number, OTP.used == False)
            result = await session.execute(query)
            otp = result.scalar_one_or_none()
            if otp:
                logger.error(f"OTP already exists for phone number {phone_number}.")
                raise OTPAlreadyExistsError()
            logger.info(f"No existing OTP found for phone number {phone_number}.")
            return False
        
        except Exception as e:
            logger.error(f"Error checking OTP for phone number {phone_number}: {e}")
            raise


    @staticmethod
    async def generate_and_send_otp(session: AsyncSession, phone_number: str, api_key: str):
        otp = f"{random.randint(1000, 9999)}"
        # send OTP via whatsapp 
        url = "https://www.wasenderapi.com/api/send-message"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "to": f"+961{phone_number}",
            "text": f"Your OTP is: {otp}."
        }
        async with httpx.AsyncClient() as client:
            request = await client.post(url, json=data, headers=headers)
            
        if request.status_code == 200:
            logger.info(f"request response: {request.text}")
        else:
            logger.error(f"Failed to send OTP via whatsapp. Status code: {request.status_code}, Response: {request.text}")
            raise ErrorSendingOTP()
        
        try:
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
            # save OTP to the database
            otp_entry = OTP(phone_number=phone_number, otp=otp, expires_at=expires_at.replace(tzinfo=None))
            session.add(otp_entry)
            logger.info(f"OTP generated and saved for phone number {phone_number}: {otp}")
            await session.commit()

            return otp
        
        except httpx.HTTPStatusError as e:
            logger.error(f"Error sending OTP via whatsapp: {e}")
            raise ErrorSendingOTP()

        except Exception as e:
            await session.rollback()
            logger.error(f"Error saving OTP for phone number {phone_number}: {e}")
            raise


    @staticmethod
    async def validate_otp(session: AsyncSession, phone_number: str, otp: str):
        try:
            query = select(OTP).where(OTP.phone_number == phone_number, OTP.otp == otp, OTP.used == False, OTP.expires_at > datetime.now(timezone.utc).replace(tzinfo=None))
            result = await session.execute(query)
            otp_entry = result.scalar_one_or_none()
            if not otp_entry:
                logger.error(f"Invalid OTP for phone number {phone_number}.")
                raise OTPInvalidError()
            
            # Mark OTP as used
            otp_entry.used = True
            await session.commit()
            logger.info(f"OTP validated and marked as used for phone number {phone_number}.")
            return True

        except Exception as e:
            await session.rollback()
            logger.error(f"Error validating OTP for phone number {phone_number}: {e}")
            raise
    

    @staticmethod
    async def generate_password_reset_token(session: AsyncSession, phone_number: str, expires_in_minutes: int = 5):
        try:
            reset_token = secrets.token_urlsafe(24)
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)

            password_reset_entry = PasswordReset(
                phone_number=phone_number,
                token=reset_token,
                expires_at=expires_at.replace(tzinfo=None)
            )
            session.add(password_reset_entry)
            await session.commit()
            logger.info(f"Password reset token generated and saved for phone number {phone_number}")
            return {
                "reset_token": reset_token,
                "expires_at": expires_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Error generating password reset token for phone number {phone_number}: {e}")
            await session.rollback()
            raise


    @staticmethod
    async def validate_password_reset_token(session: AsyncSession, phone_number: str, reset_token: str):
        try:
            query = select(PasswordReset).where(
                PasswordReset.phone_number == phone_number,
                PasswordReset.token == reset_token,
                PasswordReset.used == False,
                PasswordReset.expires_at > datetime.now(timezone.utc).replace(tzinfo=None)
            )
            result = await session.execute(query)
            reset_entry = result.scalar_one_or_none()
            if not reset_entry:
                logger.error(f"Invalid or expired password reset token for phone number {phone_number}.")
                raise InvalidResetTokenError()

            # Mark token as used
            reset_entry.used = True
            reset_entry.used_at = datetime.now(timezone.utc).replace(tzinfo=None)
            await session.commit()
            logger.info(f"Password reset token validated and marked as used for phone number {phone_number}.")

            return True
        
        except Exception as e:
            await session.rollback()
            logger.error(f"Error validating password reset token for phone number {phone_number}: {e}")
            raise


    @staticmethod
    async def send_message_to_user(phone_number: str, message: str, api_key: str):
        try:
            await asyncio.sleep(6)
            url = "https://www.wasenderapi.com/api/send-message"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "to": f"+961{phone_number}",
                "text": message
            }
            async with httpx.AsyncClient() as client:
                request = await client.post(url, json=data, headers=headers)
                
            if request.status_code == 200:
                logger.info(f"request response: {request.text}")
            else:
                logger.error(f"Failed to message to user whatsapp. Status code: {request.status_code}, Response: {request.text}")
                raise 

        except Exception as e:
            logger.error(f"Error sending message to {phone_number}: {e}")
            raise
