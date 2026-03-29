from pydantic import BaseModel, Field, field_validator, model_validator
from decimal import Decimal
from uuid import UUID
from datetime import datetime, date
from typing import Self


class CreatePaymentSchema(BaseModel):
    bill_id: UUID = Field(..., description="ID of the bill being paid")
    amount_lbp: float = Field(None, gt=0, description="Payment amount (must be positive) in lbp")
    amount_usd: float = Field(None, gt=0, description="Payment amount (must be positive) in usd")
    payment_method: str = Field(..., description="Payment method (cash, bank_transfer, check, etc.)")
    payment_date: date = Field(..., description="Date of the payment")  # Changed to date type


    @field_validator('payment_date', mode='before')
    @classmethod
    def validate_payment_date(cls, value):
        if isinstance(value, str):
            try:
                # Validate AND convert to date object
                parsed_date = datetime.strptime(value, "%Y-%m-%d")
                return parsed_date.date()  
            except ValueError:
                raise ValueError("Invalid payment date format. Must be yyyy-mm-dd.")
        elif isinstance(value, date):
            return value
        else:
            raise ValueError("Payment date must be a valid date")


    @field_validator('payment_method')
    @classmethod
    def validate_payment_method(cls, v: str) -> str:
        allowed_methods = ['cash', 'whish', 'omt']
        if v.lower() not in allowed_methods:
            raise ValueError(f"Payment method must be one of: {', '.join(allowed_methods)}")
        return v.lower()


    @field_validator('amount_usd')
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v is not None:  # Only validate if value is provided
            if v <= 0:
                raise ValueError("Payment amount must be positive")
            v = round(v, 2)
        return v
    
    
    @model_validator(mode="after")
    def check_amounts(self) -> Self:  # Fixed signature: takes self and returns Self
        if self.amount_lbp is None and self.amount_usd is None:
            raise ValueError("At least one payment amount (amount_lbp or amount_usd) must be provided")

        # only one should be provided
        if self.amount_lbp is not None and self.amount_usd is not None:
            raise ValueError("Only one payment amount (amount_lbp or amount_usd) must be provided")

        return self


    class Config:
        extra = "forbid"
