from pydantic import BaseModel, Field
from uuid import UUID

class GetMeterRequestPath(BaseModel):
    meter_id: UUID = Field(..., description="The ID of the meter to retrieve")

    class Config:
        extra = "forbid"