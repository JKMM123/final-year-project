from pydantic import BaseModel, Field
from uuid import UUID



class DeleteAreaRequestPath(BaseModel):
    area_id: UUID = Field(..., description="ID of the area to be deleted")

    class Config:
        extra = "forbid"
