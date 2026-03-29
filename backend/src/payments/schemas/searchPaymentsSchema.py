from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from zoneinfo import ZoneInfo


class SearchPaymentsSchema(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=10, ge=1, le=100, description="Number of items per page")
    
    # Filter fields
    bill_id: Optional[int] = Field(None, description="Filter by bill ID")
    meter_id: Optional[int] = Field(None, description="Filter by meter ID")
    customer_name: Optional[str] = Field(None, description="Filter by customer name (partial match)")
    meter_number: Optional[str] = Field(None, description="Filter by meter number")
    payment_method: Optional[str] = Field(None, description="Filter by payment method")
    
    # Amount range filters
    min_amount: Optional[Decimal] = Field(None, ge=0, description="Minimum payment amount")
    max_amount: Optional[Decimal] = Field(None, ge=0, description="Maximum payment amount")
    
    # Date range filters
    payment_date_from: Optional[datetime] = Field(None, description="Filter payments from this date (Asia/Beirut timezone)")
    payment_date_to: Optional[datetime] = Field(None, description="Filter payments until this date (Asia/Beirut timezone)")
    
    # Reference number filter
    reference_number: Optional[str] = Field(None, description="Filter by reference number (partial match)")
    
    # Sorting
    sort_by: str = Field(default="payment_date", description="Field to sort by")
    sort_order: str = Field(default="desc", description="Sort order (asc or desc)")

    @field_validator('payment_method')
    @classmethod
    def validate_payment_method(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed_methods = ['cash', 'bank_transfer', 'check', 'credit_card', 'debit_card', 'mobile_payment']
            if v.lower() not in allowed_methods:
                raise ValueError(f"Payment method must be one of: {', '.join(allowed_methods)}")
            return v.lower()
        return v

    @field_validator('sort_by')
    @classmethod
    def validate_sort_by(cls, v: str) -> str:
        allowed_fields = [
            'payment_date', 'amount', 'created_at', 'updated_at',
            'bill_id', 'meter_id', 'payment_method', 'reference_number'
        ]
        if v not in allowed_fields:
            raise ValueError(f"Sort field must be one of: {', '.join(allowed_fields)}")
        return v

    @field_validator('sort_order')
    @classmethod
    def validate_sort_order(cls, v: str) -> str:
        if v.lower() not in ['asc', 'desc']:
            raise ValueError("Sort order must be 'asc' or 'desc'")
        return v.lower()

    @field_validator('payment_date_from', 'payment_date_to')
    @classmethod
    def validate_timezone(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is not None:
            if v.tzinfo is None:
                raise ValueError("DateTime must include timezone information")
            # Ensure timezone is Asia/Beirut
            beirut_tz = ZoneInfo("Asia/Beirut")
            if v.tzinfo != beirut_tz:
                raise ValueError("DateTime must be in Asia/Beirut timezone")
        return v

    @field_validator('min_amount', 'max_amount')
    @classmethod
    def validate_amount(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None:
            if v < 0:
                raise ValueError("Amount filters must be non-negative")
            # Limit to 2 decimal places for currency
            if v.as_tuple().exponent < -2:
                raise ValueError("Amount cannot have more than 2 decimal places")
        return v

    @field_validator('customer_name', 'meter_number', 'reference_number')
    @classmethod
    def validate_search_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
            if len(v) > 100:
                raise ValueError("Search strings cannot exceed 100 characters")
        return v

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }
