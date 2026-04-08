from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class DashboardSummaryQuery(BaseModel):
    month: str = Field(..., description="Month in yyyy-mm format to get dashboard metrics for")

    @field_validator('month')
    def validate_month(cls, value):
        if not value:
            return value
        try:
            # Validate yyyy-mm format
            datetime.strptime(value, "%Y-%m")
        except ValueError:
            raise ValueError("Invalid month format. Must be yyyy-mm.")
        return value

    class Config:
        extra = "forbid"
