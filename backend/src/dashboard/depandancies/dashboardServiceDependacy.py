from fastapi import Request
from src.dashboard.services.dashboardService import DashboardService


async def get_dashboard_service(request: Request) -> DashboardService:
    return request.app.state.dashboard_service
