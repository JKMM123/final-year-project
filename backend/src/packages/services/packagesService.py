from fastapi import Request
from globals.utils.requestValidation import validate_request
from globals.utils.logger import logger
from globals.responses.responses import success_response
from globals.exceptions.global_exceptions import ValidationError, InternalServerError
from sqlalchemy.ext.asyncio import AsyncSession

from src.packages.queries.packagesQueries import PackagesQueries

from src.packages.exceptions.exceptions import (
    PackagesNotFoundError,
    PackageAlreadyExistsError,
    PackageInUseError
)

from src.packages.schemas.searchPackagesSchema import SearchPackagesRequestQuery
from src.packages.schemas.createPackageSchema import CreatePackageRequestBody
from src.packages.schemas.updatePackageSchema import UpdatePackageRequestBody
from src.packages.schemas.getPackageSchema import GetPackageRequestPath


class PackagesService:
    def __init__(self, packages_queries: PackagesQueries):
        self.packages_queries = packages_queries
        logger.info(f"Packages Service initialized successfully. ")

    
    async def create_package(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            body_model=CreatePackageRequestBody
        )
        if not valid:
            raise ValidationError(errors=validated_request)
        
        try:
            token = request.state.user
            package_data = validated_request.get('body')
            package_data.update(
                {
                    "created_by": token.get('user_id'),
                    "updated_by": token.get('user_id')
                }
            )
            package = await self.packages_queries.create_package(session, package_data)
            return success_response(
                message="Package created successfully.",
                data=package
            )
        
        except (
            PackageAlreadyExistsError,
            PackageInUseError
        ):
            raise

        except Exception as e:
            logger.error(f"Error creating package: {e}")
            raise InternalServerError(message="An error occurred while creating the package.")


    async def get_package(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            path_model=GetPackageRequestPath
        )
        if not valid:
            raise ValidationError(errors=validated_request)
        
        try:
            package = await self.packages_queries.get_package_by_id(session, validated_request.get('path').get('package_id'))

            return success_response(
                message="Package retrieved successfully.",
                data=package
            )
        
        except PackagesNotFoundError:
            raise

        except Exception as e:
            logger.error(f"Error getting package: {e}")
            raise InternalServerError(message="An error occurred while getting the package.")


    async def update_package(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            path_model=GetPackageRequestPath,
            body_model=UpdatePackageRequestBody
        )
        if not valid:
            raise ValidationError(errors=validated_request)
        
        try:
            token = request.state.user
            update_data = validated_request.get('body')
            update_data.update(
                {
                    "updated_by": token.get('user_id')
                }
            )
            package_id = validated_request.get('path').get('package_id')
            updated_package = await self.packages_queries.update_package(
                session, 
                package_id, 
                update_data
            )
            return success_response(
                message="Package updated successfully.",
                data=updated_package
            )

        except (
            PackagesNotFoundError,
            PackageAlreadyExistsError
        ):
            raise

        except Exception as e:
            logger.error(f"Error updating package: {e}")
            raise InternalServerError(message="An error occurred while updating the package.")


    async def delete_package(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            path_model=GetPackageRequestPath
        )
        if not valid:
            raise ValidationError(errors=validated_request)
        
        try:
            await self.packages_queries.delete_package(
                session,
                validated_request.get('path').get('package_id')
            )
            return success_response(
                message="Package deleted successfully.",
                data=[]
            )

        except (
            PackagesNotFoundError,
            PackageInUseError
        ):
            raise

        except Exception as e:
            logger.error(f"Error deleting package: {e}")
            raise InternalServerError(message="An error occurred while deleting the package.")


    async def search_packages(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            query_model=SearchPackagesRequestQuery
        )
        if not valid:
            raise ValidationError(errors=validated_request)
        
        try:
            packages = await self.packages_queries.search_packages(
                session=session,
                amperage=validated_request.get('query').get('amperage', None),
                page=validated_request.get('query').get('page', 1),
                limit=validated_request.get('query').get('limit', 10)
            )
            return success_response(
                message="Packages retrieved successfully.",
                data=packages
            )

        except Exception as e:
            logger.error(f"Error searching packages: {e}")
            raise InternalServerError(message="An error occurred while searching for packages.")