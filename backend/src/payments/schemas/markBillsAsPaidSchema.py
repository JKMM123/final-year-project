from pydantic import BaseModel, Field, field_validator
from uuid import UUID


class MarkBillsAsPaidSchema(BaseModel):
    meter_id: UUID = Field(..., description="ID of the meter whose bills are to be marked as paid")
    payment_method: str = Field(..., description="Method of payment used to mark bills as paid")
    

    model_config = {
        "extra": "forbid"
    }

    @field_validator('payment_method')
    @classmethod
    def validate_payment_method(cls, v: str) -> str:
        allowed_methods = ['cash', 'whish', 'omt']
        if v.lower() not in allowed_methods:
            raise ValueError(f"Payment method must be one of: {', '.join(allowed_methods)}")
        return v.lower()

