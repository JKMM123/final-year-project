from pydantic import BaseModel, Field
from uuid import UUID


class GetFixRequestPath(BaseModel):
    fix_id: UUID = Field(..., description="The ID of the fix to retrieve")

    class Config:
        extra = "forbid"
