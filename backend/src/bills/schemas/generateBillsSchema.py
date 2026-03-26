from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from uuid import UUID


class GenerateBillsSchema(BaseModel):
    """
    Schema for generating bills.
    """
    force_missing_meter : Optional[bool] = Field(
        default=False,
    )
    force_unverified_readings : Optional[bool] = Field(
        default=False
    )
    billing_date: str = Field(
        ...,
    )
    rate_id: UUID = Field(
        ...,
        description="The ID of the rates to be applied."
    )

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
        