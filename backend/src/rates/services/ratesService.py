from fastapi import Request
from globals.utils.requestValidation import validate_request
from globals.utils.logger import logger
from globals.responses.responses import success_response
from globals.exceptions.global_exceptions import ValidationError, InternalServerError
from sqlalchemy.ext.asyncio import AsyncSession


from src.rates.queries.ratesQueries import RatesQueries

from src.rates.exceptions.exec import (
    RatesException,
    RateNotFoundError
)

from src.rates.schemas.updateRatesSchema import UpdateRatesRequestPath, UpdateRatesSchema
from src.rates.schemas.createRatesSchemas import CreateRates
from src.rates.schemas.getRates import GetRates, GetAllRates

class RatesService:
    def __init__(self, rates_queries: RatesQueries):
        self.rates_queries = rates_queries
        logger.info(f"Rates Service initialized successfully. ")


    async def create_rates(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            body_model=CreateRates
        )
        if not valid:
            logger.error(f"Validation error in create_rates: {validated_request}")
            raise ValidationError(validated_request)
        
        try:
            token = request.state.user
            rate_data = validated_request.get("body")
            rate_data.update(
                {
                    "created_by": token.get('user_id'),
                    "updated_by": token.get('user_id')
                }
            )
            new_rates = await self.rates_queries.create_rates(session, rate_data)
            return success_response(
                message="Rates created successfully.",
                data=new_rates
            )
        
        except RatesException: 
            raise
        
        except Exception as e:
            logger.error(f"Error creating rates: {e}")
            raise InternalServerError("An error occurred while creating rates.")

    
    async def get_rates_by_date(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            path_model=GetRates
        )
        if not valid:
            logger.error(f"Validation error in get_rates_by_date: {validated_request}")
            raise ValidationError(validated_request)
        try:
            effective_date = validated_request.get('path').get('effective_date')
            rates = await self.rates_queries.get_rates_by_date(effective_date, session)
            return success_response(
                message="Rates fetched successfully.",
                data=rates
            )

        except (
            RatesException,
            RateNotFoundError
        ):
            raise
        
        except Exception as e:
            logger.error(f"Error fetching rates: {e}")
            raise InternalServerError("An error occurred while fetching rates.")



    async def update_rates(self, request: Request, session: AsyncSession):
        
        valid, validated_request = await validate_request(
            request=request,
            body_model=UpdateRatesSchema,
            path_model=UpdateRatesRequestPath
        )
        if not valid:
            logger.error(f"Validation error in update_rates: {validated_request}")
            raise ValidationError(validated_request)
        
        try:
            token = request.state.user
            rate_data = validated_request.get("body")
            rate_data.update(
                {
                    "updated_by": token.get('user_id'),
                    "rate_id": validated_request.get('path').get('rate_id')
                }
            )
            
            updated_rates = await self.rates_queries.update_rates(session, rate_data)
            return success_response(
                message="Rates updated successfully.",
                data=updated_rates
            )

        except RatesException:
            raise

        
        except Exception as e:
            logger.error(f"Error updating rates: {e}")
            raise InternalServerError("An error occurred while updating rates.")


    async def delete_rates(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            path_model=UpdateRatesRequestPath
        )
        if not valid:
            logger.error(f"Validation error in delete_rates: {validated_request}")
            raise ValidationError(validated_request)
        
        try:
            rate_id = validated_request.get('path').get('rate_id')
            await self.rates_queries.delete_rates(session, rate_id)
            return success_response(
                message="Rates deleted successfully.",
                data=[]
            )

        except RatesException:
            raise
        
        except Exception as e:
            logger.error(f"Error deleting rates: {e}")
            raise InternalServerError("An error occurred while deleting rates.")
        

    async def get_all_rates_by_year(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            path_model=GetAllRates
        )
        if not valid:
            logger.error(f"Validation error in get_all_rates_by_year: {validated_request}")
            raise ValidationError(validated_request)
        try:
            year = validated_request.get('path').get('year')
            rates = await self.rates_queries.list_all_rates_by_year(session, year)
            return success_response(
                message="Rates fetched successfully.",
                data=rates
            )

        except (
            RatesException
        ):
            raise

        except Exception as e:
            logger.error(f"Error fetching rates: {e}")
            raise InternalServerError("An error occurred while fetching rates.")
