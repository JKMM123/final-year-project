from fastapi import Request
from globals.utils.requestValidation import validate_request
from globals.utils.logger import logger
from globals.responses.responses import success_response
from globals.exceptions.global_exceptions import ValidationError, InternalServerError
from sqlalchemy.ext.asyncio import AsyncSession

from src.dashboard.queries.dashboardQueries import DashboardQueries
from src.dashboard.schemas.dashboardSummarySchema import DashboardSummaryQuery


class DashboardService:
    def __init__(self, dashboard_queries: DashboardQueries):
        self.dashboard_queries = dashboard_queries
        logger.info("Dashboard Service initialized successfully.")


    async def get_dashboard_summary(self, request: Request, session: AsyncSession):
        valid, validated_request = await validate_request(
            request=request,
            query_model=DashboardSummaryQuery
        )
        if not valid:
            logger.error(f"Validation failed in get_dashboard_summary: {validated_request}")
            raise ValidationError(errors=validated_request)

        try:
            month = validated_request.get('query').get('month')
            summary = await self.dashboard_queries.get_dashboard_summary(
                session=session, 
                month=month
            )
            return success_response(
                message="Dashboard summary retrieved successfully.",
                data=summary
            )

        except Exception as e:
            logger.error(f"Error retrieving dashboard summary: {e}")
            raise InternalServerError("Error retrieving dashboard summary.")

