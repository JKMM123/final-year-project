
from fastapi import Request
from src.areas.queries.areasQueries import AreasQueries
from globals.utils.logger import logger
from sqlalchemy.ext.asyncio import AsyncSession
from globals.utils.requestValidation import validate_request
from globals.exceptions.global_exceptions import ValidationError,InternalServerError


from src.areas.schemas.createAreaSchemas import CreateAreaRequestBody
from src.areas.schemas.deleteAreaShemas import DeleteAreaRequestPath
from src.areas.schemas.searchAreasSchemas import SearchAreasRequestParams
from src.areas.schemas.updateAreaSchemas import (
    UpdateAreaRequestPath, 
    UpdateAreaRequestBody
)

from src.areas.exceptions.exceptions import (
    AreaAlreadyExistsException,
    AreaNotFoundException,
    AreaLinkedToMetersException
)

from globals.responses.responses import success_response


class AreasService:
    def __init__(self, areas_queries: AreasQueries):
        self.areas_queries = areas_queries
        logger.info("AreasService initialized successfully.")


    async def create_area(self, request: Request, session: AsyncSession):
        """
        Create a new area.
        """
        valid, validated_request = await validate_request(
            request,
            body_model=CreateAreaRequestBody
        )
        if not valid:
            logger.error(f"Validation failed for create_area: {validated_request}")
            raise ValidationError(
                message="Validation Error while creating area.",
                errors=validated_request
            )
        
        try:
            
            token = request.state.user
        
            new_area_data = await self.areas_queries.create_area_query(
                area_name=validated_request.get('body').get("area_name"),
                elevation=validated_request.get('body').get("elevation"),
                created_by=token.get("user_id"),
                session=session
            )

            return success_response(
                message="Area created successfully.",
                data=new_area_data
            )

        except (
            AreaAlreadyExistsException
            ):
            raise

        except Exception as e:
            logger.error(f"Error creating area: {e}")
            raise InternalServerError(
                message="An error occurred while creating the area.",
            )
        

    async def delete_area(self, request: Request, session: AsyncSession):
        """
        Delete an area by ID.
        """

        valid, validated_request = await validate_request(
            request=request,
            path_model=DeleteAreaRequestPath
        )
        if not valid:
            logger.error(f"Validation failed for delete_area: {validated_request}")
            raise ValidationError(
                message="Validation Error while deleting area.",
                errors=validated_request
            )
        
        try:
            delete_area = await self.areas_queries.delete_area_query(
                area_id=str(validated_request.get('path').get("area_id")),
                session=session
            )
            return success_response(
                message="Area deleted successfully.",
                data=[]
            )
            
        except (
            AreaNotFoundException,
            AreaLinkedToMetersException
            ):
            raise   

        except Exception as e:
            logger.error(f"Error deleting area: {e}")
            raise InternalServerError(
                message="An error occurred while deleting the area.",
            )
        

    async def search_areas(self, request: Request, session: AsyncSession):
        """
        Search for areas based on query parameters.
        """
        
        valid, validated_request = await validate_request(
            request=request,
            query_model=SearchAreasRequestParams  
        )
        if not valid:
            logger.error(f"Validation failed for search_areas: {validated_request}")
            raise ValidationError(
                message="Validation Error while searching areas.",
                errors=validated_request
            )
        try:
            areas = await self.areas_queries.search_areas_query(
                search_query=validated_request.get('query').get("query"),
                page=validated_request.get('query').get("page"),
                limit=validated_request.get('query').get("limit"),
                session=session
            )

            return success_response(
                message="Areas retrieved successfully.",
                data=areas
            )

        except Exception as e:
            logger.error(f"Error searching areas: {e}")
            raise InternalServerError(
                message="An error occurred while searching for areas.",
            )
        

    async def update_area(self, request: Request, session: AsyncSession):
        """
        Update an existing area.
        """
        valid, validated_request = await validate_request(
            request=request,
            path_model=UpdateAreaRequestPath,
            body_model=UpdateAreaRequestBody
        )
        if not valid:
            logger.error(f"Validation failed for update_area: {validated_request}")
            raise ValidationError(
                message="Validation Error while updating area.",
                errors=validated_request
            )
        try:
            token = request.state.user

            area_id = str(validated_request.get('path').get("area_id"))
            area_name = validated_request.get('body').get("area_name")
            elevation = validated_request.get('body').get("elevation")
            updated_by = token.get("user_id")

            updated_area_data = await self.areas_queries.update_area_query(
                area_id=area_id,
                area_name=area_name,
                elevation=elevation,
                updated_by=updated_by,
                session=session
            )

            return success_response(
                message="Area updated successfully.",
                data=updated_area_data
            )

        except (
            AreaNotFoundException,
            AreaAlreadyExistsException
            ):
            raise

        except Exception as e:
            logger.error(f"Error updating area: {e}")
            raise InternalServerError(
                message="An error occurred while updating the area.",
            )
        
