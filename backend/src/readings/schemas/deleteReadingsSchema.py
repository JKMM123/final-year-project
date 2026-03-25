from pydantic import BaseModel, Field
from uuid import UUID
from typing import List


class DeleteReadingsRequestBody(BaseModel):
    reading_ids: List[UUID] = Field(..., description="List of reading IDs to delete", min_length=1)

    class Config:
        extra = "forbid"