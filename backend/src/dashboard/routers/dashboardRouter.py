from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from db.postgres.dependancies import get_async_session

from src.dashboard.services.dashboardService import DashboardService
from src.dashboard.depandancies.dashboardServiceDependacy import get_dashboard_service


dashboard_router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["dashboard"],
)


@dashboard_router.get("/summary", response_model=dict)
async def get_dashboard_summary(
    request: Request,
    dashboard_service: DashboardService = Depends(get_dashboard_service),
    session: AsyncSession = Depends(get_async_session)
):
    return await dashboard_service.get_dashboard_summary(request, session)

