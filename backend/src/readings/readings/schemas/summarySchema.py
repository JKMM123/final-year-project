from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class ReadingsSummaryQuery(BaseModel):
    reading_date: str = Field(..., description="Filter by reading date")

    @field_validator('reading_date')
    def validate_reading_date(cls, value):
        if not value:
            return value
        try:
            # Validate yyyy-mm format
            datetime.strptime(value, "%Y-%m")
        except ValueError:
            raise ValueError("Invalid reading date format. Must be yyyy-mm.")
        return value

    class Config:
        extra = "forbid"
