from pydantic import BaseModel, Field
from uuid import UUID
from typing import List


class DeleteFixesRequestBody(BaseModel):
    fix_ids: List[UUID] = Field(..., description="List of fix IDs to delete", min_length=1)

    class Config:
        extra = "forbid"
