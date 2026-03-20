from fastapi import Request, UploadFile
from globals.utils.requestValidation import validate_request
from globals.utils.logger import logger
from globals.responses.responses import success_response
from globals.exceptions.global_exceptions import ValidationError, InternalServerError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from globals.utils.fileValidator import FileValidator, FileValidationConfigs
from io import BytesIO
 

from src.readings.queries.readingsQueries import ReadingsQueries
from src.readings.schemas.createReadingSchema import CreateReadingRequestBody
from src.readings.schemas.getReadingSchema import GetReadingRequestPath
from src.readings.schemas.updateReadingSchema import UpdateReadingRequestBody, ReadingStatusUpdate, VerifyAllReadings
from src.readings.schemas.searchReadingsSchema import SearchReadingsRequestBody
from src.readings.schemas.summarySchema import ReadingsSummaryQuery
from src.readings.schemas.deleteReadingsSchema import DeleteReadingsRequestBody


from src.readings.exceptions.exceptions import (
    ReadingNotFoundException,
    ReadingAlreadyVerifiedException,
    DuplicateReadingDateException,
    ReadingFrequencyException,
    InvalidReadingValueException,
    FixedMeterCannotHaveUsageReadingsError,
)

from src.meters.exceptions.exceptions import (
    MeterNotFoundError,
    MeterInactiveError
)

from src.users.exceptions.exceptions import (
    InsufficientPermissionsException
)

class ReadingsService:
    def __init__(self, readings_queries: ReadingsQueries):
        self.readings_queries = readings_queries
        logger.info(f"Readings Service initialized successfully.")

    async def create_reading(self, request: Request, reading: Optional[UploadFile], session: AsyncSession):
        await FileValidator.validate_file(
                file=reading,
                **FileValidationConfigs.IMAGES,
                require_file=True
            )
        valid, validated_request = await validate_request(
            request=request,
            query_model=CreateReadingRequestBody
        )
        if not valid:
            logger.error(f"Validation failed in create_reading: {validated_request}")
            raise ValidationError(errors=validated_request)

        try:
            token = request.state.user
            image_bytes = await reading.read()
            reading_data = validated_request.get('query')
            reading_data.update({
                "created_by": token.get('user_id'),
                "updated_by": token.get('user_id')
            })
            reading = await self.readings_queries.create_reading(
                session=session,
                reading_data=reading_data,
                image_bytes=BytesIO(image_bytes)
            )
            return success_response(
                message="Reading created successfully.",
                data=reading
            )
        except (
            DuplicateReadingDateException,
            InvalidReadingValueException,
            ReadingFrequencyException,
            MeterNotFoundError,
            InvalidReadingValueException,
            FixedMeterCannotHaveUsageReadingsError,
            MeterInactiveError
            ):
            raise

        except Exception as e:
            logger.error(f"Error occurred while creating reading: {e}")
            raise InternalServerError(message="An error occurred while creating reading.")


    async def get_reading(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            path_model=GetReadingRequestPath
        )
        if not valid:
            logger.error(f"Validation failed in get_reading: {validated_request}")
            raise ValidationError(errors=validated_request)
        try:
            reading_id = validated_request.get('path').get('reading_id')
            reading = await self.readings_queries.get_reading_by_id(
                session=session,
                reading_id=reading_id
            )
            return success_response(
                message="Reading retrieved successfully.",
                data=reading
            )
        except ReadingNotFoundException:
            raise

        except Exception as e:
            logger.error(f"Error occurred while retrieving reading: {e}")
            raise InternalServerError(message="An error occurred while retrieving reading.")


    async def update_reading(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            path_model=GetReadingRequestPath,
            body_model=UpdateReadingRequestBody
        )
        if not valid:
            logger.error(f"Validation failed in update_reading: {validated_request}")
            raise ValidationError(errors=validated_request)
        
        token = request.state.user
        reading_id = validated_request.get('path').get('reading_id')
        update_data = validated_request.get('body')
        update_data.update({
            "updated_by": token.get('user_id')
        })

        if update_data.get('status') == 'verified':
            user_role = token.get('role')
            if not ReadingStatusUpdate.can_update_status(user_role):
                logger.error(f"Permission denied: {user_role} cannot update readings.")
                raise InsufficientPermissionsException(
                    message=f"'{user_role}' cannot verify readings."
                )
        try:
            reading = await self.readings_queries.update_reading(
                session=session,
                reading_id=reading_id,
                update_data=update_data
            )
            return success_response(
                message="Reading updated successfully.",
                data=reading
            )
        except (
            ReadingNotFoundException,
            ReadingAlreadyVerifiedException,
            MeterNotFoundError
        ):
            raise

        except Exception as e:
            logger.error(f"Error occurred while updating reading: {e}")
            raise InternalServerError(message="An error occurred while updating reading.")


    async def delete_reading(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            path_model=GetReadingRequestPath
        )
        if not valid:
            logger.error(f"Validation failed in delete_reading: {validated_request}")
            raise ValidationError(errors=validated_request)
        try:
            reading_id = validated_request.get('path').get('reading_id')
            await self.readings_queries.delete_reading(
                session=session,
                reading_id=reading_id
            )
            return success_response(
                message="Reading deleted successfully.",
                data=[]
            )
        
        except ReadingNotFoundException:
            raise

        except Exception as e:
            logger.error(f"Error occurred while deleting reading: {e}")
            raise InternalServerError(message="An error occurred while deleting reading.")


    async def search_readings(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            body_model=SearchReadingsRequestBody
        )
        if not valid:
            logger.error(f"Validation failed in search_readings: {validated_request}")
            raise ValidationError(errors=validated_request)
        try:
            filters = validated_request.get('body', {})
            readings = await self.readings_queries.search_readings(
                session=session,
                filters=filters
            )
            return success_response(
                message="Readings retrieved successfully.",
                data=readings
            )
        
        except Exception as e:
            logger.error(f"Error occurred while searching readings: {e}")
            raise InternalServerError(message="An error occurred while searching readings.")
        

    async def get_readings_summary(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            query_model=ReadingsSummaryQuery
        )
        if not valid:
            logger.error(f"Validation failed in get_untaken_readings: {validated_request}")
            raise ValidationError(errors=validated_request)

        try:
            readings_summary = await self.readings_queries.get_readings_summary(
                session=session,
                reading_date=validated_request.get('query').get('reading_date'),
            )
            return success_response(
                message="Readings summary retrieved successfully.",
                data=readings_summary
            )

        except Exception as e:
            logger.error(f"Error occurred while retrieving readings summary: {e}")
            raise InternalServerError(message="An error occurred while retrieving readings summary.")
        

    async def verify_all_readings(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            body_model=VerifyAllReadings
        )
        if not valid:
            logger.error(f"Validation failed in verify_all_readings: {validated_request}")
            raise ValidationError(errors=validated_request)
        
        token = request.state.user
        user_role = token.get('role')
        if not ReadingStatusUpdate.can_update_status(user_role):
            logger.error(f"Permission denied: {user_role} cannot verify readings.")
            raise InsufficientPermissionsException(
                message=f"'{user_role}' cannot verify readings."
            )
        
        confirm = validated_request.get('body').get('confirm')
        if not confirm:
            raise ValidationError(errors={
                "field": "confirm",
                "message": "Are you sure you want to verify all readings?"
                })

        try:
                        
            verified_count = await self.readings_queries.verify_all_readings(
                session=session,
                reading_date=validated_request.get('body').get('reading_date'),
                verified_by=token.get('user_id')
            )
            return success_response(
                message=f"Readings verified successfully.",
                data={"verified_count": verified_count}
            )

        except Exception as e:
            logger.error(f"Error occurred while verifying all readings: {e}")
            raise InternalServerError(message="An error occurred while verifying all readings.")



    # async def delete_readings(self, request: Request, session: AsyncSession):
    #     valid, validated_request = await validate_request(
    #         request=request,
    #         body_model=DeleteReadingsRequestBody
    #     )
    #     if not valid:
    #         logger.error(f"Validation failed in delete_readings: {validated_request}")
    #         raise ValidationError(errors=validated_request)

    #     try:
    #         filters = validated_request.get('body', {})
    #         await self.readings_queries.delete_readings(
    #             session=session,
    #             filters=filters
    #         )
    #         return success_response(
    #             message="Readings deleted successfully.",
    #             data=[]
    #         )

    #     except Exception as e:
    #         logger.error(f"Error occurred while deleting readings: {e}")
    #         raise InternalServerError(message="An error occurred while deleting readings.")

