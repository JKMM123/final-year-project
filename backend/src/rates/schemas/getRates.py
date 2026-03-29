from pydantic import BaseModel, Field, field_validator
from datetime import datetime, date

class GetRates(BaseModel):
    effective_date: str = Field(..., description="The date for which the rates are applicable in YYYY-MM-DD format.")

    @field_validator('effective_date')
    def validate_effective_date(cls, value):
        try:
            datetime.strptime(value, "%Y-%m")
        except ValueError:
            raise ValueError("Invalid billing date format. Must be yyyy-mm.")
        return value

    class Config:
        extra = "forbid"



class GetAllRates(BaseModel):
    year: int = Field(..., description="The year for which to retrieve all rates.", ge=2000, le=date.today().year)

    @field_validator('year')
    def validate_year(cls, value):
        current_year = date.today().year
        if value < 2000 or value > current_year:
            raise ValueError(f"Year must be between 2000 and {current_year}.")
        return value

    class Config:
        extra = "forbid"
