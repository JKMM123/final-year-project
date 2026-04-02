from fastapi import Request
from globals.utils.requestValidation import validate_request
from globals.utils.logger import logger
from globals.responses.responses import success_response
from globals.exceptions.global_exceptions import ValidationError, InternalServerError
from sqlalchemy.ext.asyncio import AsyncSession

from src.templates.schemas.createTemplateSchema import CreateTemplateRequestBody
from src.templates.schemas.updateTemplateSchema import UpdateTemplateRequestPath, UpdateTemplateRequestBody
from src.templates.schemas.getTemplateSchema import GetTemplateRequestPath
from src.templates.schemas.deleteTemplateSchema import DeleteTemplateRequestPath
from src.templates.schemas.searchTemplatesSchema import SearchTemplatesRequestQuery
from src.templates.queries.templatesQueries import TemplatesQueries
 
from src.templates.exceptions.exceptions import (
    TemplateNotFoundError,
    TemplateAlreadyExistsError,
    InvalidAreasProvidedError,
    InvalidCustomersProvidedError,
    InvalidPackagesProvidedError,
)


class TemplatesService:
    def __init__(self):
        self.templates_queries = TemplatesQueries()
        logger.info("TemplatesService initialized successfully")


    async def create_template(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            body_model=CreateTemplateRequestBody
        )
        if not valid:
            logger.error(f"Validation failed in create_template: {validated_request}")
            raise ValidationError(errors=validated_request)
        
        try:
            token = request.state.user
            template_data = validated_request.get('body')
            template_data.update(
                created_by=token.get('user_id'),
            )

            created_template = await self.templates_queries.create_template(
                session=session,
                template_data=template_data
            )
            
            return success_response(
                message="Template created successfully.",
                data=created_template
            )
        
        except (
            TemplateAlreadyExistsError,
            InvalidAreasProvidedError,
            InvalidCustomersProvidedError,
            InvalidPackagesProvidedError,
        ):
            raise

        except Exception as e:
            logger.error(f"Error in create_template: {e}")
            raise InternalServerError("An error occurred while creating the template.")


    async def get_template(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            path_model=GetTemplateRequestPath
        )
        if not valid:
            logger.error(f"Validation failed in get_template: {validated_request}")
            raise ValidationError(errors=validated_request)
        
        try:
            template_id = str(validated_request.get('path').get('template_id'))
            
            template = await self.templates_queries.get_template_by_id(
                session=session,
                template_id=template_id
            )
            
            return success_response(
                message="Template fetched successfully.",
                data=template
            )
        
        except TemplateNotFoundError:
            raise

        except Exception as e:
            logger.error(f"Error in get_template: {e}")
            raise InternalServerError("An error occurred while fetching the template.")


    async def update_template(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            path_model=UpdateTemplateRequestPath,
            body_model=UpdateTemplateRequestBody
        )
        if not valid:
            logger.error(f"Validation failed in update_template: {validated_request}")
            raise ValidationError(errors=validated_request)
        
        try:
            token = request.state.user  
            template_id = str(validated_request.get('path').get('template_id'))
            update_data = validated_request.get('body')
            update_data.update(
                updated_by=token.get('user_id'),
            )

            updated_template = await self.templates_queries.update_template(
                session=session,
                template_id=template_id,
                update_data=update_data
            )
            
            return success_response(
                message="Template updated successfully.",
                data=updated_template
            )
        
        except (TemplateNotFoundError, TemplateAlreadyExistsError):
            raise
        
        except Exception as e:
            logger.error(f"Error in update_template: {e}")
            raise InternalServerError("An error occurred while updating the template.")


    async def delete_template(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            path_model=DeleteTemplateRequestPath
        )
        if not valid:
            logger.error(f"Validation failed in delete_template: {validated_request}")
            raise ValidationError(errors=validated_request)
        
        try:
            template_id = str(validated_request.get('path').get('template_id'))
            
            deleted_template = await self.templates_queries.delete_template(
                session=session,
                template_id=template_id
            )
            
            return success_response(
                message="Template deleted successfully.",
                data=[]
            )
        
        except TemplateNotFoundError:
            raise

        except Exception as e:
            logger.error(f"Error in delete_template: {e}")
            raise InternalServerError("An error occurred while deleting the template.")


    async def search_templates(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            query_model=SearchTemplatesRequestQuery
        )
        if not valid:
            logger.error(f"Validation failed in search_templates: {validated_request}")
            raise ValidationError(errors=validated_request)
        
        try:
            filters = validated_request.get('query')
            
            templates = await self.templates_queries.search_templates(
                session=session,
                filters=filters
            )
            
            return success_response(
                message="Templates fetched successfully.",
                data=templates
            )
        
        except Exception as e:
            logger.error(f"Error in search_templates: {e}")
            raise InternalServerError("An error occurred while searching templates.")
