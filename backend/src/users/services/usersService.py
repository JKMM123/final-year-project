from fastapi import Request
from globals.utils.requestValidation import validate_request
from globals.utils.logger import logger
from globals.responses.responses import success_response
from globals.exceptions.global_exceptions import ValidationError, InternalServerError
from sqlalchemy.ext.asyncio import AsyncSession


from src.users.schemas.createUserSchema import CreateUserRequestBody, UserRole
from src.users.schemas.updateUserSchema import UpdateUserRequestPath, UpdateUserRequestBody
from src.users.schemas.deleteUserSchema import DeleteUserRequestPath
from src.users.schemas.getUserSchema import GetUserRequestPath
from src.users.schemas.searchUsersSchema import SearchUsersRequestQuery
from src.users.queries.usersQueries import UsersQueries

from globals.config.config import DEFAULT_PASSWORD
from globals.utils.hashingHelper import HashingHelper

from src.users.exceptions.exceptions import (
    UserNotFoundError,
    UsernameAlreadyExistsError,
    PhoneNumberAlreadyExistsError,
    InsufficientPermissionsException
)
from src.auth.services.otpService import OTPService
from globals.config.config import FRONT_END_URL

from src.messages.queries.whatsAppSessionQueries import WhatsAppSessionQueries

from src.messages.exceptions.exceptions import (
    WhatsAppSessionNotFoundError
)

class UsersService:
    def __init__(self, users_queries: UsersQueries):
        self.users_queries = users_queries
        self.whatsapp_session_queries = WhatsAppSessionQueries()
        logger.info("UsersService initialized successfully")


    async def create_user(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            body_model=CreateUserRequestBody
        )
        if not valid:
            logger.error(f"Validation failed in create_user: {validated_request}")
            raise ValidationError(
                errors=validated_request
            )
        
        token = request.state.user
        creator_role = token.get('role')
        target_role = validated_request.get('body').get('role').lower()
        
        if not UserRole.can_create_role(creator_role, target_role):
                logger.error(f"Permission denied: {creator_role} cannot create {target_role}")
                raise InsufficientPermissionsException(
                    message=f"'{creator_role}' cannot create user with role '{target_role}'"
                    )

        try: 
            body = validated_request.get("body")
            body.update(
                {
                    "password_hash": HashingHelper.generate_hash(DEFAULT_PASSWORD),
                    "created_by": token.get('user_id'),
                    "updated_by": token.get('user_id')
                }
            )
            user = await self.users_queries.create_user(
                session=session,
                user_data=body
            )
            whatsapp_session = await self.whatsapp_session_queries.get_session(session=session)
            # send message to user
            await OTPService.send_message_to_user(
                phone_number=body.get("phone_number"),
                message=f"Hello {body.get('username')}, an account has been created for you. To secure your access, please set your own password now using the following link: {FRONT_END_URL}/reset-password",
                api_key=whatsapp_session.api_key
            )
            return success_response(
                data=user,
                message="User created successfully."
            )
        
        except (
            UsernameAlreadyExistsError,
            PhoneNumberAlreadyExistsError
        ):
            raise 

        except Exception as e:
            logger.error(f"Error in create_user: {str(e)}")
            raise InternalServerError(
                message="An error occurred while creating the user."
            )


    async def get_user(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            path_model=GetUserRequestPath
        )
        if not valid:
            logger.error(f"Validation failed in get_user: {validated_request}")
            raise ValidationError(
                errors=validated_request
            )
        try:
            token = request.state.user
            user = await self.users_queries.get_user_by_id(
                user_role=token.get('role'),
                session=session,
                user_id=validated_request.get("path").get("user_id")
            )
            return success_response(
                data=user,
                message="User retrieved successfully."
            )
        
        except UserNotFoundError:
            raise 

        except Exception as e:
            logger.error(f"Error in get_user: {str(e)}")
            raise InternalServerError(
                message="An error occurred while retrieving the user."
            )


    async def update_user(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            path_model=UpdateUserRequestPath,
            body_model=UpdateUserRequestBody
        )
        if not valid:
            logger.error(f"Validation failed in update_user: {validated_request}")
            raise ValidationError(
                errors=validated_request
            )
        
        token = request.state.user
        creator_role = token.get('role')
        user = await self.users_queries.get_user_by_id(
            user_role=creator_role,
            session=session,
            user_id=validated_request.get("path").get("user_id")
        )
        target_role = user.get('role').lower()
        
        if not UserRole.can_update_role(creator_role, target_role):
                logger.error(f"Permission denied: {creator_role} cannot update {target_role}")
                raise InsufficientPermissionsException(
                    message=f"'{creator_role}' cannot update user with role '{target_role}'"
                    )
        
        updated_role = validated_request.get("body").get("role").lower()
        if not UserRole.can_update_role(creator_role, updated_role):
            logger.error(f"Permission denied: {creator_role} cannot update to {updated_role}")
            raise InsufficientPermissionsException(
                message=f"'{creator_role}' cannot update user to role '{updated_role}'"
            )

        try:
            body = validated_request.get("body")
            body.update(
                {
                    "updated_by": token.get('user_id')
                }
            )
            updated_user = await self.users_queries.update_user(
                session=session,
                user_id=validated_request.get("path").get("user_id"),
                update_data=body
            )
            return success_response(
                data=updated_user,
                message="User updated successfully."
            )
        except (
            UsernameAlreadyExistsError,
            PhoneNumberAlreadyExistsError,
            UserNotFoundError
        ):
            raise
        
        except Exception as e:
            logger.error(f"Error in update_user: {str(e)}")
            raise InternalServerError(
                message="An error occurred while updating the user."
            )


    async def delete_user(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            path_model=DeleteUserRequestPath
        )
        if not valid:
            logger.error(f"Validation failed in delete_user: {validated_request}")
            raise ValidationError(
                errors=validated_request
            )
        
        token = request.state.user
        creator_role = token.get('role')
        user = await self.users_queries.get_user_by_id(
            user_role=creator_role,
            session=session,
            user_id=validated_request.get("path").get("user_id")
        )
        target_role = user.get('role').lower()  
        if not UserRole.can_delete_role(creator_role, target_role):
                logger.error(f"Permission denied: {creator_role} cannot delete {target_role}")
                raise InsufficientPermissionsException(
                    message=f"'{creator_role}' cannot delete user with role '{target_role}'"
                    )
        
        try:
            await self.users_queries.delete_user(
                session=session,
                user_id=validated_request.get("path").get("user_id")
            )
            return success_response(
                message="User deleted successfully.",
                data=[]
            )
        
        except UserNotFoundError:
            raise

        except Exception as e:
            logger.error(f"Error in delete_user: {str(e)}")
            raise InternalServerError(
                message="An error occurred while deleting the user."
            )


    async def search_users(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            query_model=SearchUsersRequestQuery
        )
        if not valid:
            logger.error(f"Validation failed in search_users: {validated_request}")
            raise ValidationError(
                errors=validated_request
            )
        try:
            token = request.state.user
            users = await self.users_queries.search_users(
                user_role=token.get('role'),
                session=session,
                query=validated_request.get("query").get("query"),
                role=validated_request.get("query").get("role"),
                page=validated_request.get("query").get("page"),
                limit=validated_request.get("query").get("limit")
            )
            return success_response(
                data=users,
                message="Users retrieved successfully."
            )

        except Exception as e:
            logger.error(f"Error in search_users: {str(e)}")
            raise InternalServerError(
                message="An error occurred while searching for users."
            )
