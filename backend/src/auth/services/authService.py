from fastapi import Request
from globals.utils.requestValidation import validate_request
from globals.utils.logger import logger
from globals.responses.responses import success_response
from globals.exceptions.global_exceptions import ValidationError, InternalServerError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schemas.loginSchema import LoginRequestBody
from src.auth.schemas.otpSchemas import (
    SendOTPQueryParamsRequestBody,
    VerifyOTPQueryParamsRequestBody
)
from src.auth.schemas.resetPasswordSchemas import ResetPasswordRequestBody
from src.auth.queries.authQueries import AuthQueries

from globals.exceptions.global_exceptions import UnauthorizedError

from src.auth.exceptions.exceptions import (
    UsernameOrPhoneNotFoundError,
    InvalidPasswordError, 
    OTPAlreadyExistsError,
    OTPInvalidError, 
    InvalidResetTokenError,
    ErrorSendingOTP
)
from src.auth.services.otpService import OTPService
from src.messages.queries.whatsAppSessionQueries import WhatsAppSessionQueries

from src.messages.exceptions.exceptions import (
    WhatsAppSessionNotFoundError
)

class AuthService:
    def __init__(self, auth_queries: AuthQueries):
        self.auth_queries = auth_queries
        self.whatsapp_session_queries = WhatsAppSessionQueries()
        logger.info("AuthService initialized successfully")


    async def login(self, request: Request, session: AsyncSession):    
        valid, validated_request = await validate_request(
            request=request, 
            body_model=LoginRequestBody
            )

        if not valid:
            logger.error(f"validation error in login: {validated_request}")
            raise ValidationError(
                errors=validated_request
            )
        try:
            username_or_phone = validated_request.get('body').get('username_or_phone')
            password = validated_request.get('body').get('password')

            user_data = await self.auth_queries.login_query(
                username_or_phone=username_or_phone,
                password=password,
                session=session,
                device_id=validated_request.get('body').get('device_id')
            )
 
            response = success_response(
                message="Signed In Successfully",
                data=user_data.get('user_info')
            )

            response.set_cookie(
                key="access_token",
                value=user_data.get('tokens').get('access_token'),
                httponly=True,
                # secure=True,
                samesite='lax',
                max_age= 60 * 60 # 1 hour in seconds
            )

            response.set_cookie(
                key="refresh_token",
                value=user_data.get('tokens').get('refresh_token'),
                httponly=True,
                # secure=True,
                samesite='lax',
                max_age = 60 * 60 * 24 * 10  # 10 days in seconds
            )

            return response

        except (
            ValidationError,
            UsernameOrPhoneNotFoundError,
            InvalidPasswordError
        ):
            raise

        except Exception as e:
            logger.error(f"Error in login: {str(e)}")
            raise InternalServerError(
                message="An error occurred while processing your login request."
            )


    async def logout(self, request: Request, session: AsyncSession):
        try:
            user = request.state.user
            await self.auth_queries.logout_query(
                session=session,
                user_id=user.get('user_id'),
                device_id=user.get('device_id')
            )
            response = success_response(
                message="Logged Out Successfully",
                data=[]
            )
            response.delete_cookie(key="access_token")
            response.delete_cookie(key="refresh_token")
            logger.info(f"User {user.get('user_id')} logged out successfully.")
            return response

        except Exception as e:
            logger.error(f"Error in logout: {str(e)}")
            raise InternalServerError(
                message="An error occurred while processing your logout request."
            )
        

    async def get_me(self, request: Request):
        try:
            user = request.state.user
            user_info = {
                "user_id": user.get('user_id'),
                "username": user.get('username'),
                "phone_number": user.get('phone_number'),
                "role": user.get('role')
            }
            return success_response(
                message="User data retrieved successfully.",
                data=user_info
            )
        except Exception as e:
            logger.error(f"Error in get_me: {str(e)}")
            raise InternalServerError(
                message="An error occurred while retrieving user data."
            )


    async def refresh(self, request: Request, session: AsyncSession):
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            logger.error("Refresh token not found in cookies.")
            raise ValidationError(
                message="Refresh token is required for refreshing access token.",
                errors=[]
            )
        try:
            user = request.state.user
            new_access_token = await self.auth_queries.refresh_query(
                user_id=user.get('user_id'),
                device_id=user.get('device_id'),
                decoded_jwt=user,
                session=session
            )
            response = success_response(
                message="Access token refreshed successfully.",
                data=[]
            )
            response.set_cookie(
                key="access_token",
                value=new_access_token,
                httponly=True,
                # secure=True,
                samesite='lax',
                max_age=60 * 60  # 1 hour in seconds
            )
            return response
        
        except UnauthorizedError:
            raise
        
        except Exception as e:
            logger.error(f"Error in refresh: {str(e)}")
            raise InternalServerError(
                message="An error occurred while refreshing the access token."
            )
        

    async def validate_token(self, request: Request, session: AsyncSession):
        try:
            user = request.state.user
            
            return success_response(
                message="Token is valid.",
                data=[]
            )
        
        except Exception as e:
            logger.error(f"Error in validate_token: {str(e)}")
            raise InternalServerError(
                message="An error occurred while validating the token."
            )


    async def reset_password(self, request: Request, session: AsyncSession):
        
        valid, validated_request = await validate_request(
            request=request,
            body_model=ResetPasswordRequestBody
        )
        if not valid:
            logger.error(f"Validation failed in reset_password: {validated_request}")
            raise ValidationError(errors=validated_request)
        
        try:
            reset_token = validated_request.get('body').get('reset_token')
            phone_number = validated_request.get('body').get('phone_number')
            new_password = validated_request.get('body').get('new_password')

            user = await self.auth_queries.get_user_by_phone(
                session=session,
                phone_number=phone_number
            )

            validate_token = await OTPService.validate_password_reset_token(
                session=session,
                phone_number=phone_number,
                reset_token=reset_token
            )

            if not user:
                raise UsernameOrPhoneNotFoundError()

            await self.auth_queries.reset_password_query(
                session=session,
                phone_number=phone_number,
                new_password=new_password
            )

            return success_response(
                message="Password reset successfully.",
                data=[]
            )
        
        except (
            UsernameOrPhoneNotFoundError,
            InvalidResetTokenError
        ):
            raise

        except Exception as e:
            logger.error(f"Error in reset_password: {str(e)}")
            raise InternalServerError(
                message="An error occurred while resetting the password."
            )


    async def send_otp(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            query_model=SendOTPQueryParamsRequestBody
        )
        if not valid:
            logger.error(f"Validation failed in send_otp: {validated_request}")
            raise ValidationError(errors=validated_request)

        try:
            phone_number = validated_request.get('query').get('phone_number')

            user = await self.auth_queries.get_user_by_phone(
                session=session,
                phone_number=phone_number
            )
            whatsapp_session = await self.whatsapp_session_queries.get_session(session)
            
            succes = await OTPService.generate_and_send_otp(
                session=session,
                phone_number=phone_number,
                api_key=whatsapp_session.api_key 
            )

            if not succes:
                raise InternalServerError(
                    message="Failed to generate or send OTP."
                )

            return success_response(
                message="OTP sent successfully.",
                data=[]
            )

        except (
            UsernameOrPhoneNotFoundError,
            OTPAlreadyExistsError,
            ErrorSendingOTP,
            WhatsAppSessionNotFoundError,
        ):
            raise

        except Exception as e:
            logger.error(f"Error in send_otp: {str(e)}")
            raise InternalServerError(
                message="An error occurred while sending the OTP."
            )
        

    async def verify_otp(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            body_model=VerifyOTPQueryParamsRequestBody
        )
        if not valid:
            logger.error(f"Validation failed in verify_otp: {validated_request}")
            raise ValidationError(errors=validated_request)

        try:
            phone_number = validated_request.get('body').get('phone_number')
            otp = validated_request.get('body').get('otp')

            otp_validated = await OTPService.validate_otp(
                session=session,
                phone_number=phone_number,
                otp=otp
            )

            reset_token = await OTPService.generate_password_reset_token(
                session=session,
                phone_number=phone_number
            )

            return success_response(
                message="OTP verified successfully.",
                data=reset_token
            )

        except OTPInvalidError:
            raise

        except Exception as e:
            logger.error(f"Error in verify_otp: {str(e)}")
            raise InternalServerError(
                message="An error occurred while verifying the OTP."
            )

