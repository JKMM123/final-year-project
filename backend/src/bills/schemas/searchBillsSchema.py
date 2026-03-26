from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import datetime, date
from typing import Optional, List
import re


class SearchBillsRequestBody(BaseModel):
    due_date: str = Field(
        ..., description="The due date of the bill"
    )
    status: Optional[List[str]] = Field(
        None, description="The status of the bill"
    )
    query: Optional[str] = Field(
        None, description="Search term for customer name or phone number"
    )
    payment_method: Optional[List[str]] = Field(
        None, description="Filter bills by payment method"
    )
    page: Optional[int] = Field(1, ge=1, description="Page number for pagination")
    limit: Optional[int] = Field(10, ge=1, le=30, description="Number of readings per page")

    @field_validator('status')
    def validate_status(cls, value):
        allowed_statuses = ['unpaid', 'paid', 'partially_paid']
        for status in value or []:
            if status not in allowed_statuses:
                raise ValueError(f"Invalid status: {status}. Allowed values are {allowed_statuses}.")
        return value
    
    @field_validator('payment_method')
    def validate_payment_method(cls, value):
        allowed_methods = ['cash', 'whish', 'omt']
        for method in value or []:
            if method.lower() not in allowed_methods:
                raise ValueError(f"Invalid payment method: {method}. Allowed values are {allowed_methods}.")
        return [method.lower() for method in value]

    @field_validator('due_date')
    def validate_due_date(cls, value):
        if not value:
            return value
        try:
            # Validate yyyy-mm format
            datetime.strptime(value, "%Y-%m")
        except ValueError:
            raise ValueError("Invalid billing date format. Must be yyyy-mm.")
        return value
        
        
    @field_validator('query')
    def validate_query(cls, v):
        v = v.strip()
        if not v:
            return v
            
        # Allow Arabic, English, numbers, spaces, _ and -
        if not re.fullmatch(r"^[\u0600-\u06FFa-zA-Z0-9_-]+(\s[\u0600-\u06FFa-zA-Z0-9_-]+)*$", v):
            raise ValueError("Invalid query format. Only Arabic, English letters, numbers, spaces, _ and - are allowed.")
        return v

    class Config:
        extra = "forbid"
