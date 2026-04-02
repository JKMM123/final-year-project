from pydantic import BaseModel, Field, model_validator, field_validator
from uuid import UUID
from typing import Optional
from zoneinfo import ZoneInfo
from datetime import datetime, date


class MeterFilters(BaseModel):
    """Filters based on meter/customer data"""
    area_ids: list[UUID] | None = Field(None, description="Filter by area IDs", min_length=1, max_length=100)
    package_ids: list[UUID] | None = Field(None, description="Filter by package IDs", min_length=1, max_length=100)
    package_type: str | None = Field(None, description="Filter by package type", pattern=r"^(fixed|usage|all)$")
    meter_status: str | None = Field(None, description="Filter by meter status", pattern=r"^(active|inactive|all)$")

    class Config:
        extra = "forbid"


class BillFilters(BaseModel):
    """Filters based on bill data"""
    due_date: str = Field(..., description="Filter by due date")
    payment_status: str | None = Field(None, description="Filter by payment status", pattern=r"^(paid|unpaid|partially_paid|all)$")
    payment_method: list[str] | None = Field(None, description="Filter by payment methods")
    overdue_only: bool | None = Field(None, description="Filter only overdue bills")

    @field_validator('payment_method')
    def validate_payment_method(cls, v):
        if v is None:
            return v
        allowed_values = {"cash", "whish", "omt", "all"}
        for item in v:
            if item not in allowed_values:
                raise ValueError(f"payment_method item '{item}' must be one of: {', '.join(allowed_values)}")
        return v
    
    @field_validator('due_date')
    def validate_due_date(cls, value):
        try:
            # Validate yyyy-mm format
            datetime.strptime(value, "%Y-%m")
        except ValueError:
            raise ValueError("Invalid reading date format. Must be yyyy-mm.")
        return value

    @model_validator(mode="after") 
    def validate_logical_combinations(cls, values):
        overdue_only = values.overdue_only
        payment_status = values.payment_status
        payment_method = values.payment_method

         # Overdue bills are always unpaid
        if overdue_only is True: 
            if payment_status is None:
                values.payment_status = "unpaid"

            if payment_method is not None:
                raise ValueError("Overdue bills can't have payment methods")
            
        # Payment status validations
        if payment_status == "paid":
            if payment_method is None:
                values.payment_method = ["all"]

        elif payment_status == "unpaid":
            if payment_method is not None:
                values.payment_method = None  
            
        # Payment method validations
        if payment_method is not None:
            # Can't mix "all" with specific methods
            if "all" in payment_method and len(payment_method) > 1:
                raise ValueError("payment_method 'all' cannot be combined with specific methods")
            
            # Auto-correct: if payment_method specified but no status, assume "paid"
            if payment_status is None and "all" not in payment_method:
                values.payment_status = "paid"
        
        return values


    class Config:
        extra = "forbid"


class sendMessagesRequestBody(BaseModel):
    """Combined filter structure - use either meter_filters OR bill_filters OR both"""
    meter_filters: Optional[MeterFilters] = Field(None, description="Meter-based filters")
    bill_filters: Optional[BillFilters] = Field(None, description="Bill-based filters")
    template_id: Optional[UUID] = Field(None, description="The ID of the message template to use")
    message: Optional[str] = Field(None, description="The message content")
    broadcast: bool = Field(False, description="Whether to broadcast the message to all customers")
    customer_ids: list[UUID] | None = Field(
        None, 
        description="Send to specific customers (overrides other filters)", 
        min_length=1
    )
    send_immediately: bool = Field(True, description="Send immediately or schedule")
    scheduled_at: str | None = Field(
        None, 
        description="Schedule send time (ISO format)", 
    )

    @field_validator('scheduled_at')
    @classmethod
    def validate_scheduled_at_timezone(cls, v):
        if v is None:
            return v
            
        beirut_tz = ZoneInfo('Asia/Beirut')
        
        try:
            # Parse the datetime string
            dt = datetime.fromisoformat(v)
            
            # Must have timezone info
            if dt.tzinfo is None:
                raise ValueError("scheduled_at must include timezone information (+02:00 or +03:00 for Asia/Beirut)")
            
            # Accept if the UTC offset matches Asia/Beirut at that date/time
            # Beirut uses +02:00 (winter) or +03:00 (summer DST)
            beirut_equivalent = dt.astimezone(beirut_tz)
            if dt.utcoffset() != beirut_equivalent.utcoffset():
                actual_offset = dt.utcoffset()
                expected_offset = beirut_equivalent.utcoffset()
                raise ValueError(f"Only Asia/Beirut timezone offsets accepted. Expected {expected_offset}, got {actual_offset}")
            
            # Ensure it's in the future (compare in Beirut timezone)
            now_beirut = datetime.now(beirut_tz)
            if dt.astimezone(beirut_tz) <= now_beirut:
                raise ValueError("scheduled_at must be in the future (Asia/Beirut time)")
            
            # Store the original input for later UTC conversion
            return v
                
        except ValueError as e:
            if any(msg in str(e) for msg in ["timezone", "future", "offset"]):
                raise e
            raise ValueError(f"Invalid datetime format for scheduled_at: {e}")


    @model_validator(mode="after")
    def validate_message_template(cls, values):
        template_id = values.template_id
        message = values.message

        if template_id is None and message is None:
            raise ValueError("Must specify either template_id or message")

        if template_id is not None and message is not None:
            raise ValueError("Must specify either template_id or message, not both")

        return values

    @model_validator(mode="after")
    def validate_message_targeting(cls, values):
        broadcast = values.broadcast
        customer_ids = values.customer_ids
        meter_filters = values.meter_filters
        bill_filters = values.bill_filters

        # Rule 1: If broadcast is True, no other filters allowed
        if broadcast:
            if customer_ids or meter_filters or bill_filters:
                raise ValueError("When broadcast=true, customers and filters must be empty")
            return values
        
        # Rule 2: If customer_ids provided, ignore other filters (specific targeting)
        if customer_ids:
            if len(customer_ids) > 1000:
                raise ValueError("Cannot send to more than 1000 specific customers at once")
            # Clear other filters when using specific customer targeting
            values.meter_filters = None
            values.bill_filters = None
            return values
        
        # Rule 3: If not broadcast and no customer_ids, must have at least one filter
        meter_has_data = meter_filters and any(v is not None for v in meter_filters.model_dump().values())
        bill_has_data = bill_filters and any(v is not None for v in bill_filters.model_dump().values())

        if not meter_has_data and not bill_has_data:
            raise ValueError(
                "Must specify either broadcast=true, customer_ids, or at least one filter group "
                "(meter_filters or bill_filters)"
            )
        
        return values


    @model_validator(mode="after")
    def validate_scheduling(cls, values):
        if not values.send_immediately and not values.scheduled_at:
            raise ValueError("If send_immediately=false, scheduled_at must be provided")
        
        if values.send_immediately and values.scheduled_at:
            raise ValueError("Cannot set both send_immediately=true and scheduled_at")
        
        return values
        
    class Config:
        extra = "forbid"

