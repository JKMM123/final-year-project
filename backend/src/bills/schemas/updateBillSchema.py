from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional

class UpdateBillRequestBody(BaseModel):
    status: str = Field(
        ..., description="The new status of the bill"
    )
    payment_method: Optional[str] = Field(
        None, description="The payment method used for the bill"
    )

    @field_validator('status')
    def validate_status(cls, value):
        allowed_statuses = ['unpaid', 'paid']
        if value not in allowed_statuses:
            raise ValueError(f"Invalid status: {value}. Allowed values are {allowed_statuses}.")
        return value
    
    @field_validator('payment_method')
    def validate_payment_method(cls, value):
        allowed_methods = ['cash', 'whish', 'omt']
        if value.lower() not in allowed_methods:
            raise ValueError(f"Invalid payment method: {value}. Allowed values are {allowed_methods}.")
        return value.lower() 
    
    @model_validator(mode="after")
    def check_payment_method_if_paid(self):
        if self.status != "paid":
            self.payment_method = None
        if self.status == "paid" and (not self.payment_method or self.payment_method.strip() == ""):
            raise ValueError("Payment method must be provided when status is 'paid'.")
        
        return self
    
    class Config:
        extra = "forbid"
