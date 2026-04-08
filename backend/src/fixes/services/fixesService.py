from fastapi import Request, UploadFile
from globals.utils.requestValidation import validate_request
from globals.utils.logger import logger
from globals.responses.responses import success_response
from globals.exceptions.global_exceptions import ValidationError, InternalServerError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional



from globals.utils.logger import logger
from globals.responses.responses import success_response
from globals.utils.requestValidation import validate_request
from globals.exceptions.global_exceptions import ValidationError, InternalServerError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request
from uuid import UUID

from src.fixes.queries.fixesQueries import FixesQueries
from src.fixes.schemas.createFixSchema import CreateFixRequestBody
from src.fixes.schemas.deleteFixSchema import DeleteFixesRequestBody
from src.fixes.schemas.getFixSchema import GetFixRequestPath
from src.fixes.schemas.updateFixSchema import UpdateFixRequestBody, UpdateFixRequestPath
from src.fixes.schemas.searchFixesSchema import SearchFixesRequestBody

from src.fixes.exceptions.exceptions import (
    FixNotFoundError,
    MeterInactiveError,
    MeterNotFoundError
)


class FixesService:
    def __init__(self, fixes_queries: FixesQueries):
        self.fixes_queries = fixes_queries
        logger.info("Fixes Service initialized successfully.")


    async def create_fix(self, request: Request, session: AsyncSession):
        """Create a new fix"""
        valid, validated_request = await validate_request(
            request=request,
            body_model=CreateFixRequestBody
        )
        if not valid:
            logger.error(f"Validation error in create_fix: {validated_request}")
            raise ValidationError(errors=validated_request)

        try:
            token = request.state.user
            fix_data = validated_request.get('body')

            new_fix = await self.fixes_queries.create_fix(
                session=session,
                fix_data=fix_data,
                user_id=token.get('user_id')
            )
            
            return success_response(
                message="Fix created successfully",
                data={
                    "fix_id": str(new_fix.fix_id),
                    "meter_id": str(new_fix.meter_id),
                    "fix_date": str(new_fix.fix_date),
                    "description": new_fix.description,
                    "cost": float(new_fix.cost),
                    "created_at": new_fix.created_at.isoformat()
                }
            )
            
        except (
            MeterNotFoundError,
            MeterInactiveError,
            FixNotFoundError
            ):
            raise

        except Exception as e:
            logger.error(f"Error occurred while creating fix: {e}")
            raise InternalServerError("Error occurred while creating fix")


    async def get_fix(self, request: Request, session: AsyncSession):
        """Get a specific fix by ID"""
        valid, validated_request = await validate_request(
            request=request,
            path_model=GetFixRequestPath
        )
        if not valid:
            logger.error(f"Validation error in get_fix: {validated_request}")
            raise ValidationError(errors=validated_request)

        try:
            fix_id = validated_request.get('path').get('fix_id')

            fix = await self.fixes_queries.get_fix_by_id(
                session=session,
                fix_id=fix_id
            )
            
            return success_response(
                message="Fix retrieved successfully",
                data=fix
            )
            
        except FixNotFoundError:
            raise

        except Exception as e:
            logger.error(f"Error occurred while getting fix: {e}")
            raise InternalServerError("Error occurred while getting fix")


    async def update_fix(self, request: Request, session: AsyncSession):
        """Update an existing fix"""
        valid, validated_request = await validate_request(
            request=request,
            body_model=UpdateFixRequestBody,
            path_model=UpdateFixRequestPath
        )
        if not valid:
            logger.error(f"Validation error in update_fix: {validated_request}")
            raise ValidationError(errors=validated_request)

        try:
            token = request.state.user
            fix_id = validated_request.get('path').get('fix_id')
            fix_data = validated_request.get('body')

            updated_fix = await self.fixes_queries.update_fix(
                session=session,
                fix_id=fix_id,
                fix_data=fix_data,
                user_id=token.get('user_id')
            )
            
            return success_response(
                message="Fix updated successfully",
                data=[]
            )
            
        except FixNotFoundError:
            raise

        except Exception as e:
            logger.error(f"Error occurred while updating fix: {e}")
            raise InternalServerError("Error occurred while updating fix")


    async def delete_fixes(self, request: Request, session: AsyncSession):
        """Delete multiple fixes"""
        valid, validated_request = await validate_request(
            request=request,
            body_model=DeleteFixesRequestBody
        )
        if not valid:
            logger.error(f"Validation error in delete_fixes: {validated_request}")
            raise ValidationError(errors=validated_request)

        try:
            fix_ids = validated_request.get('body').get('fix_ids')

            await self.fixes_queries.delete_fixes(
                session=session,
                fix_ids=fix_ids
            )
            
            return success_response(
                message="Fixes deleted successfully",
                data=[]
            )
            
        except FixNotFoundError:
            raise

        except Exception as e:
            logger.error(f"Error occurred while deleting fixes: {e}")
            raise InternalServerError("Error occurred while deleting fixes")


    async def search_fixes(self, request: Request, session: AsyncSession):
        """Search fixes with filters and pagination"""
        valid, validated_request = await validate_request(
            request=request,
            body_model=SearchFixesRequestBody
        )
        if not valid:
            logger.error(f"Validation error in search_fixes: {validated_request}")
            raise ValidationError(errors=validated_request)

        try:
            filters = validated_request.get('body')

            fixes = await self.fixes_queries.search_fixes(
                session=session,
                filters=filters
            )
            
            return success_response(
                message="Fixes retrieved successfully",
                data=fixes
            )
            
        except Exception as e:
            logger.error(f"Error occurred while searching fixes: {e}")
            raise InternalServerError("Error occurred while searching fixes")