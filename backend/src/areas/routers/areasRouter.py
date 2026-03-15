from fastapi import APIRouter, Depends, Request
from src.areas.dependancies.areasServiceDependancy import get_areas_service
from src.areas.services.areasService import AreasService
from db.postgres.dependancies import get_async_session




areas_router = APIRouter(
    prefix="/api/v1/areas",
    tags=["areas"]
)

@areas_router.post("/create")
async def create_area(
    request: Request,
    service: AreasService = Depends(get_areas_service),
    session=Depends(get_async_session)
):
    return await service.create_area(request, session)



@areas_router.get("/search")
async def search_areas(
    request: Request,
    service: AreasService = Depends(get_areas_service),
    session=Depends(get_async_session)
):
    return await service.search_areas(request, session)


@areas_router.delete("/{area_id}")
async def delete_area(
    request: Request,  
   service: AreasService = Depends(get_areas_service),
    session=Depends(get_async_session)
):
    return await service.delete_area(request, session)


@areas_router.put("/{area_id}")
async def update_area(
    request: Request,
    service: AreasService = Depends(get_areas_service),
    session=Depends(get_async_session)
): 
    return await service.update_area(request, session)