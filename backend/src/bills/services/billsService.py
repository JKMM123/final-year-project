import math
from fastapi import Request
from globals.utils.requestValidation import validate_request
from globals.utils.logger import logger
from globals.responses.responses import success_response
from globals.exceptions.global_exceptions import ValidationError, InternalServerError
from sqlalchemy.ext.asyncio import AsyncSession

from src.bills.queries.billsQueries import BillsQueries

from src.bills.schemas.getBillSchema import (
    GetBillRequestPath,
    )
from src.bills.schemas.searchBillsSchema import SearchBillsRequestBody
from src.bills.schemas.updateBillSchema import UpdateBillRequestBody
from src.bills.schemas.generateBillsSchema import GenerateBillsSchema
from src.bills.schemas.downloadBillsSchema import DownloadBillsSchema
from src.bills.schemas.getStatementSchema import GetStatementSchema


from src.bills.exceptions.exceptions import (
    BillNotFoundError,
    BillsGenerationRestrictionError,
    DeletePaidBillError
)
from src.meters.exceptions.exceptions import NoActiveMetersError, MeterNotFoundError
from src.readings.exceptions.exceptions import (
    NoReadingsFoundForActiveMetersError,
    MissingReadingsForActiveMetersError,
    UnverifiedReadingsError
)
from src.rates.exceptions.exec import (
    RateNotFoundError
)
from src.readings.exceptions.exceptions import NoReadingsFoundForActiveMetersError
from src.meters.exceptions.exceptions import NoActiveMetersError
import asyncio
from src.celery.celery_app import celery_app
from src.bills.tasks.generateBillsTask import generate_images_for_due_date
from src.bills.tasks.downloadBillsTask import generate_pdfs_for_due_date

class BillsService:
    def __init__(self, bills_queries: BillsQueries):
        self.bills_queries = bills_queries
        logger.info(f"Bills Service initialized successfully. ")


    async def generate_bills(self, request: Request, session: AsyncSession):

        valid, validated_request = await validate_request(
            request=request,
            query_model=GenerateBillsSchema
        )
        if not valid:
            logger.error(f"Validation error in generate_bills: {validated_request}")
            raise ValidationError(validated_request)
        
        try:
            token = request.state.user
            generation_results = await self.bills_queries.generate_bills(
                session=session,
                creator_id=token.get("user_id"),
                force_unverified_readings=validated_request.get('query').get("force_unverified_readings", False),
                force_missing_meter=validated_request.get('query').get("force_missing_meter", False),
                billing_date=validated_request.get('query').get("billing_date"),
                rate_id=validated_request.get('query').get("rate_id")
            )
            generated_bill_ids = generation_results.get("generated_bill_ids", [])

            if not generated_bill_ids:
                logger.info(f"No new bills generated for the specified period.")
                return success_response(
                    message=generation_results.get('message', "No new bills generated."),
                    data={
                        "metrics": generation_results.get('metrics', {}),
                        "billing_period": generation_results.get('billing_period', ""),
                        "due_date": generation_results.get('due_date', ""),
                        }
                )

            bills_full_data_for_due_date = await self.bills_queries.get_bills_full_data_for_due_date(
                session=session,
                billing_date=validated_request.get('query').get("billing_date"),
                bill_ids=generated_bill_ids,
                rate_id=validated_request.get('query').get("rate_id")
            )   
            
            if not bills_full_data_for_due_date:
                logger.info(f"No bills found for generation")
                return success_response(
                    message="No bills found for the specified due date.",
                    data=[]
                )
            total_bills = len(bills_full_data_for_due_date)
            
            # Start optimized task
            task = generate_images_for_due_date.delay(
                bills_full_data_for_due_date,
                chunk_size=25
            )

            logger.info(f"Enqueued image generation task {task.id} for {total_bills} bills")

            return success_response(
                message=f"Bills generated successfully for {total_bills} meters.",
                data={
                    "task_id": task.id,
                    "metrics": generation_results.get('metrics', {}),
                    "billing_period": generation_results.get('billing_period', ""),
                    "due_date": generation_results.get('due_date', ""),
                }
            )

        
        except (
            BillsGenerationRestrictionError,
            NoActiveMetersError,
            NoReadingsFoundForActiveMetersError,
            MissingReadingsForActiveMetersError,
            UnverifiedReadingsError,
            RateNotFoundError
        ):
            raise 

        except Exception as e:
            logger.error(f"Error in generate_bills: {e}")
            raise InternalServerError("An error occurred while generating bills.")

    
    async def get_bill(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            path_model=GetBillRequestPath
        )
        if not valid:
            logger.error(f"Validation error in get_bill: {validated_request}")
            raise ValidationError(validated_request)
        
        try:
            bill = await self.bills_queries.get_bill(
                session=session,
                bill_id=validated_request.get('path').get("bill_id")
            )
            return success_response(
                message="Bill fetched successfully.",
                data=bill
            )
        
        except BillNotFoundError:
            raise

        except Exception as e:
            logger.error(f"Error in get_bill: {e}")
            raise InternalServerError("An error occurred while fetching the bill.")


    async def search_bills(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            body_model=SearchBillsRequestBody
        )
        if not valid:
            logger.error(f"Validation error in search_bills: {validated_request}")
            raise ValidationError(validated_request)

        try:
            filters = validated_request.get('body')
            bills = await self.bills_queries.search_bills(
                session=session,
                filters=filters
            )
            return success_response(
                message="Bills fetched successfully.",
                data=bills
            )

        except Exception as e:
            logger.error(f"Error in search_bills: {e}")
            raise InternalServerError("An error occurred while searching for bills.")
 

    async def update_bill(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            path_model=GetBillRequestPath,
            body_model=UpdateBillRequestBody
        )
        if not valid:
            logger.error(f"Validation error in update_bill: {validated_request}")
            raise ValidationError(validated_request)

        try:
            updated_bill = await self.bills_queries.update_bill(
                session=session,
                bill_id=validated_request.get('path').get("bill_id"),
                data=validated_request.get('body')
            )
            return success_response(
                message="Bill updated successfully.",
                data=updated_bill
            )
        
        except BillNotFoundError:
            raise

        except Exception as e:
            logger.error(f"Error in update_bill: {e}")
            raise InternalServerError("An error occurred while updating the bill.")


    async def delete_bill(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            path_model=GetBillRequestPath
        )
        if not valid:
            logger.error(f"Validation error in delete_bill: {validated_request}")
            raise ValidationError(validated_request)

        try:
            await self.bills_queries.delete_bill(
                session=session,
                bill_id=validated_request.get('path').get("bill_id")
            )
            return success_response(
                message="Bill deleted successfully.",
                data=[]
            )
        
        except (
            BillNotFoundError,
            DeletePaidBillError
            ):
            raise

        except Exception as e:
            logger.error(f"Error in delete_bill: {e}")
            raise InternalServerError("An error occurred while deleting the bill.")


    async def download_bills(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            query_model=DownloadBillsSchema
        )
        if not valid:
            raise ValidationError(validated_request)
        
        try:
            token = request.state.user
            billing_date = validated_request.get('query').get("billing_date")
            
            bills_full_data_for_billing_date = await self.bills_queries.get_bills_full_data_for_due_date(
                session=session,
                billing_date=billing_date
            )
            if not bills_full_data_for_billing_date:
                return success_response(
                    message="No bills to download.", 
                    data=[]
                )

            user_phone_number = token.get("phone_number")
            total_bills = len(bills_full_data_for_billing_date)

            task = generate_pdfs_for_due_date.delay(
                bills_full_data_for_billing_date,
                user_phone_number=user_phone_number
            )
            logger.info(f"Enqueued PDF generation task {task.id} for {total_bills} bills")

            return success_response(
                message=f"PDF generation started for {total_bills} bills. You will receive a notification once it's complete.",
                data={
                    "task_id": task.id,
                    "total_bills": total_bills,
                }   
            )

        except Exception as e:
            logger.error(f"Error in download_bills: {e}")
            raise InternalServerError("An error occurred while downloading bills.")


    async def get_statement(self, request: Request, session: AsyncSession):
        try:
            valid, validated_request = await validate_request(
                request=request,
                query_model=GetStatementSchema
            )
            if not valid:
                logger.error(f"Validation error in get_statement: {validated_request}")
                raise ValidationError(validated_request)
                
            year = validated_request.get('query').get("year")
            meter_id = validated_request.get('query').get("meter_id")
            statement = await self.bills_queries.get_statement(
                session=session,
                meter_id=meter_id,
                year=year
            )
            return success_response(
                message="Statement fetched successfully.",
                data=statement
            )
            
        except (
            ValidationError,
            MeterNotFoundError
        ):
            raise

        except Exception as e:
            logger.error(f"Error in get_statement: {e}")
            raise InternalServerError("An error occurred while fetching the statement.")


    