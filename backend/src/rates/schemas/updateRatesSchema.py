from pydantic import BaseModel, Field
from uuid import UUID


class UpdateRatesSchema(BaseModel):
    mountain_kwh_rate: float = Field(..., description="The updated mountain kilowatt-hour rate.", ge=0)
    coastal_kwh_rate: float = Field(..., description="The updated coastal kilowatt-hour rate.", ge=0)
    dollar_rate: float = Field(..., description="The updated dollar rate.", gt=0)
    fixed_sub_rate: int = Field(..., description="Fixed subscription rate", ge=0)
    fixed_sub_hours: int = Field(..., description="Fixed subscription hours", ge=0)

    class Config:
        extra = "forbid"



class UpdateRatesRequestPath(BaseModel):
    rate_id: UUID = Field(..., description="The ID of the rate to update")

    class Config:
        extra = "forbid"