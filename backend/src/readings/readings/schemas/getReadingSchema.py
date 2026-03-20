from pydantic import BaseModel, Field
from uuid import UUID

class GetReadingRequestPath(BaseModel):
    reading_id: UUID = Field(..., description="The ID of the reading to retrieve or modify")

    class Config:
        extra = "forbid"
