from pydantic import BaseModel, Field, field_validator
from datetime import datetime

class CreateRates(BaseModel):
    mountain_kwh_rate: int = Field(..., description="The updated mountain kilowatt-hour rate.", ge=0)
    coastal_kwh_rate: int = Field(..., description="The updated coastal kilowatt-hour rate.", ge=0)
    dollar_rate: int = Field(..., description="The updated dollar rate.", gt=0)
    effective_date: str = Field(..., description="The date when the new rates become effective.")
    fixed_sub_rate: int = Field(..., description="Fixed subscription rate", ge=0)
    fixed_sub_hours: int = Field(..., description="Fixed subscription hours", ge=0)

    @field_validator('effective_date')
    def validate_effective_date(cls, value):
        try:
            datetime.strptime(value, "%Y-%m")
        except ValueError:
            raise ValueError("Invalid effective date format. Must be yyyy-mm.")
        return value

    class Config:
        extra = "forbid"



