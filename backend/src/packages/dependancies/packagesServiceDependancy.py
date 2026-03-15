from fastapi import Request
from src.packages.services.packagesService import PackagesService



async def get_packages_service(request: Request) -> PackagesService:
    return request.app.state.packages_service
