from globals.utils.logger import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select, func, delete, or_, and_
from sqlalchemy.exc import IntegrityError

from db.postgres.tables.templates import Templates
from db.postgres.tables.areas import Areas
from db.postgres.tables.packages import Packages
from db.postgres.tables.meters import Meters


from src.templates.exceptions.exceptions import (
    TemplateNotFoundError,
    TemplateAlreadyExistsError
)

 
class TemplatesQueries:
    def __init__(self):
        logger.info("Templates Queries initialized successfully.")


    async def create_template(self, session: AsyncSession, template_data: dict):
        try:

            new_template = Templates(
                name=template_data.get('name'),
                message=template_data.get('message'),
                created_by=template_data.get('created_by'),
                updated_by=template_data.get('created_by')
            )
            session.add(new_template)
            await session.commit()
            await session.refresh(new_template)
            
            logger.info(f"Template {new_template.name} created successfully.")
            return {
                "template_id": str(new_template.template_id),
                "name": new_template.name,
                "message": new_template.message,
            }
        except IntegrityError as e:
            await session.rollback()
            error_info = str(e.orig)
            
            if "uq_templates_name" in error_info:
                logger.error(f"Template with name '{template_data.get('name')}' already exists.")
                raise TemplateAlreadyExistsError("Template with this name already exists.")
            else:
                logger.error(f"Integrity error creating template: {error_info}")
                raise TemplateAlreadyExistsError("Template creation failed due to constraint violation.")
        
        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating template: {str(e)}")
            raise


    async def get_template_by_id(self, session: AsyncSession, template_id: str):
        try:
            query = select(Templates).where(Templates.template_id == template_id)
            result = await session.execute(query)
            template = result.scalar_one_or_none()
            
            if not template:
                logger.error(f"Template with ID {template_id} not found.")
                raise TemplateNotFoundError()
            
            logger.info(f"Template {template.name} fetched successfully by ID {template_id}.")
            return {
                "template_id": str(template.template_id),
                "name": template.name,
                "message": template.message,
            }

        except Exception as e:
            logger.error(f"Error fetching template by ID {template_id}: {str(e)}")
            raise


    async def update_template(self, session: AsyncSession, template_id: str, update_data: dict):
        try:
            get_template_query = select(Templates).where(Templates.template_id == template_id)
            result = await session.execute(get_template_query)
            template = result.scalar_one_or_none()
            if not template:
                logger.error(f"Template with ID {template_id} not found.")
                raise TemplateNotFoundError()
            
            template.name = update_data.get('name', template.name)
            template.message = update_data.get('message', template.message)
            template.updated_by = update_data.get('updated_by', template.updated_by)

            await session.commit()
            logger.info(f"Template {template.name} updated successfully.")
            return  {
                "template_id": str(template.template_id),
                "name": template.name,
                "message": template.message,
            }
        
        except IntegrityError as e:
            await session.rollback()
            error_info = str(e.orig)
            
            if "uq_templates_name" in error_info:
                logger.error(f"Template with name '{update_data.get('name')}' already exists.")
                raise TemplateAlreadyExistsError("Template with this name already exists.")
            else:
                logger.error(f"Integrity error updating template: {error_info}")
                raise TemplateAlreadyExistsError("Template update failed due to constraint violation.")

        except Exception as e:
            await session.rollback()
            logger.error(f"Error updating template: {str(e)}")
            raise


    async def delete_template(self, session: AsyncSession, template_id: str):
        try:
            # Check if template exists
            query = select(Templates).where(Templates.template_id == template_id)
            result = await session.execute(query)
            template = result.scalar_one_or_none()
            
            if not template:
                logger.error(f"Template with ID {template_id} not found for deletion.")
                raise TemplateNotFoundError()
            
            # Delete the template
            delete_query = delete(Templates).where(Templates.template_id == template_id)
            await session.execute(delete_query)
            await session.commit()
            
            logger.info(f"Template {template.name} deleted successfully.")
            return True
        
        except Exception as e:
            await session.rollback()
            logger.error(f"Error deleting template: {str(e)}")
            raise


    async def search_templates(self, session: AsyncSession, filters: dict):
        try:
            query = filters.get('query', '').strip() if filters.get('query') else ''
            page = filters.get('page', 1)
            limit = filters.get('limit', 10)
            offset = (page - 1) * limit
            
            # Build the base query
            stmt = select(Templates)
            conditions = []
            
            # Add search conditions
            if query:
                
                search_condition = or_(
                    Templates.name.ilike(f"%{query}%"),
                )
                conditions.append(search_condition)
        
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            # Get total count
            count_stmt = select(func.count(Templates.template_id))
            if conditions:
                count_stmt = count_stmt.where(and_(*conditions))
            
            total_result = await session.execute(count_stmt)
            total_count = total_result.scalar()
            
            # Apply pagination and ordering
            stmt = stmt.order_by(Templates.created_at.desc()).limit(limit).offset(offset)
            
            result = await session.execute(stmt)
            templates = result.scalars().all()
            
            templates_data = []
            for template in templates:
                templates_data.append({
                    "template_id": str(template.template_id),
                    "name": template.name,
                    "message": template.message
                })
            

            total_pages = (total_count + limit - 1) // limit
            has_next = page < total_pages
            has_previous = page > 1

            logger.info(f"Fetched {len(templates_data)} templates for page {page} with limit {limit}.")
            
            return {
                "templates": templates_data,
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
            logger.error(f"Error searching templates: {str(e)}")
            raise

        