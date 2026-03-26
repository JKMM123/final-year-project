from pydantic import BaseModel, Field, field_validator
from datetime import datetime, date




class DownloadBillsSchema(BaseModel):
    billing_date: str = Field(..., description="Date for which to download bills")

    @field_validator('billing_date')
    def validate_billing_date(cls, value):
        if not value:
            return value
        try:
            # Validate yyyy-mm format
            datetime.strptime(value, "%Y-%m")
        except ValueError:
            raise ValueError("Invalid billing date format. Must be yyyy-mm.")
        return value
        
    class Config:
        extra = "forbid"