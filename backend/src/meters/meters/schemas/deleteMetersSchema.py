from pydantic import BaseModel, Field
from uuid import UUID
from typing import List


class DeleteMetersRequestBody(BaseModel):
    meter_ids: List[UUID] = Field(..., description="List of meter IDs to delete", min_length=1)

    class Config:
        extra = "forbid"