from fastapi import Request
from globals.utils.requestValidation import validate_request
from globals.utils.logger import logger
from globals.responses.responses import success_response
from globals.exceptions.global_exceptions import ValidationError, InternalServerError
from sqlalchemy.ext.asyncio import AsyncSession

from src.meters.queries.metersQueries import MetersQueries

from src.meters.schemas.createMeterSchema import CreateMeterRequestBody
from src.meters.schemas.searchMetersSchema import SearchMetersRequestBody
from src.meters.schemas.getMeterSchema import GetMeterRequestPath
from src.meters.schemas.updateMeterSchema import UpdateMeterRequestBody
from src.meters.schemas.deleteMetersSchema import DeleteMetersRequestBody

from src.meters.exceptions.exceptions import (
    MeterNotFoundError,
    CustomerIdentityAddressAlreadyExistsError,
    MeterInUseError
)

from src.packages.exceptions.exceptions import PackagesNotFoundError

from src.areas.exceptions.exceptions import AreaNotFoundException


class MetersService:
    def __init__(self, meters_queries: MetersQueries):
        self.meters_queries = meters_queries
        logger.info(f"Meters Service initialized successfully. ")


    async def create_meter(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            body_model=CreateMeterRequestBody
        )
        if not valid:
            logger.error(f"Validation error: {validated_request}")
            raise ValidationError(errors=validated_request)
        
        try:
            token = request.state.user
            meter_data = validated_request.get('body')
            meter_data.update({
                "created_by": token.get('user_id'),
                "updated_by": token.get('user_id')
            })
            meter = await self.meters_queries.create_meter(
                session=session, 
                meter_data=meter_data
                )
                        
            return success_response(
                message="Meter created successfully",
                data=meter
            )
        
        except (
            PackagesNotFoundError,
            CustomerIdentityAddressAlreadyExistsError,
            AreaNotFoundException
        ):
            raise

        except Exception as e:
            logger.error(f"Error occurred while creating meter: {e}")
            raise InternalServerError("Error occurred while creating meter")
        
    
    async def search_meters(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            body_model=SearchMetersRequestBody
        )
        if not valid:
            logger.error(f"Validation error: {validated_request}")
            raise ValidationError(errors=validated_request)

        try:
            meters = await self.meters_queries.search_meters(
                session=session, 
                search_params=validated_request.get('body')
            )
            return success_response(
                message="Meters fetched successfully",
                data=meters
            )

        except Exception as e:
            logger.error(f"Error occurred while searching meters: {e}")
            raise InternalServerError("Error occurred while searching meters")
        

    async def get_meter(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            path_model=GetMeterRequestPath
        )
        if not valid:
            logger.error(f"Validation error: {validated_request}")
            raise ValidationError(errors=validated_request)

        try:
            meter = await self.meters_queries.get_meter_by_id(
                session=session, 
                meter_id=validated_request.get('path').get('meter_id')
            )
            return success_response(
                message="Meter fetched successfully",
                data=meter
            )
        
        except MeterNotFoundError:
            raise

        except Exception as e:
            logger.error(f"Error occurred while getting meter by ID: {e}")
            raise InternalServerError("Error occurred while getting meter by ID")
        

    async def update_meter(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            body_model=UpdateMeterRequestBody,
            path_model=GetMeterRequestPath
        )
        if not valid:
            logger.error(f"Validation error in update_meter: {validated_request}")
            raise ValidationError(errors=validated_request)

        try:
            token = request.state.user
            update_data = validated_request.get('body')
            update_data.update({
                "updated_by": token.get('user_id')
            })
            meter = await self.meters_queries.update_meter(
                session=session, 
                meter_id=validated_request.get('path').get('meter_id'),
                update_data=update_data
            )
            return success_response(
                message="Meter updated successfully",
                data=meter
            )
        
        except (
            PackagesNotFoundError,
            MeterNotFoundError,
            AreaNotFoundException
        ):
            raise

        except Exception as e:
            logger.error(f"Error occurred while updating meter: {e}")
            raise InternalServerError("Error occurred while updating meter")
        

    async def delete_meter(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            path_model=GetMeterRequestPath
        )
        if not valid:
            logger.error(f"Validation error: {validated_request}")
            raise ValidationError(errors=validated_request)

        try:
            await self.meters_queries.delete_meter(
                session=session, 
                meter_id=validated_request.get('path').get('meter_id')
            )
            return success_response(
                message="Meter deleted successfully",
                data=[]
            )
        
        except (
            MeterNotFoundError,
            MeterInUseError
        ):
            raise

        except Exception as e:
            logger.error(f"Error occurred while deleting meter: {e}")
            raise InternalServerError("Error occurred while deleting meter")
      
        
    async def get_meter_qr_code(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            path_model=GetMeterRequestPath
        )
        if not valid:
            logger.error(f"Validation error: {validated_request}")
            raise ValidationError(errors=validated_request)

        try:

            qr_code_url = await self.meters_queries.get_qr_code(
                session=session, 
                meter_id=validated_request.get('path').get('meter_id')
            )
            return success_response(
                message="Meter QR code fetched successfully",
                data={"qr_code_url": qr_code_url}
            )
        
        except MeterNotFoundError:
            raise

        except Exception as e:
            logger.error(f"Error occurred while getting meter QR code: {e}")
            raise InternalServerError("Error occurred while getting meter QR code")
           

    async def get_meter_qr_codes(self, request: Request, session: AsyncSession):

        try:
            zip_file_url = await self.meters_queries.get_qr_codes(
                session=session, 
            )
            return success_response(
                message="Meter QR codes fetched successfully",
                data=zip_file_url
            )

        except Exception as e:
            logger.error(f"Error occurred while getting meter QR codes: {e}")
            raise InternalServerError("Error occurred while getting meter QR codes")


    async def delete_meters(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            body_model=DeleteMetersRequestBody
        )
        if not valid:
            logger.error(f"Validation error in delete_meters: {validated_request}")
            raise ValidationError(errors=validated_request)

        try:
            meter_ids = validated_request.get('body').get('meter_ids')
            await self.meters_queries.delete_meters_query(
                session=session, 
                meter_ids=meter_ids
            )
            return success_response(
                message="Meters deleted successfully",
                data=[]
            )
        
        except (
            MeterNotFoundError,
            MeterInUseError
        ):
            raise

        except Exception as e:
            logger.error(f"Error occurred while deleting meters: {e}")
            raise InternalServerError("Error occurred while deleting meters")




    