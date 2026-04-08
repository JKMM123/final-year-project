from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import date, datetime
import re


class CreateFixRequestBody(BaseModel):
    meter_id: UUID = Field(..., description="The ID of the meter that needs fixing")
    fix_date: date = Field(..., description="The date when the fix was performed")
    description: str = Field(..., description="Description of the fix performed", min_length=1, max_length=500)
    cost: float = Field(..., description="Cost of the fix", ge=0, le=999999999.99)

    @field_validator("description")
    def validate_description(cls, v):
        if not v or not v.strip():
            raise ValueError("Description cannot be empty")
        
        # Allow Arabic, English, numbers, spaces, punctuation, and common symbols
        if not re.fullmatch(r"^[\u0600-\u06FFa-zA-Z0-9\s.,!?_()-]+$", v):
            raise ValueError("Description contains invalid characters")
        return v.strip()

    @field_validator("fix_date")
    def validate_fix_date(cls, value):
        if isinstance(value, date):
            if value > datetime.now().date():
                raise ValueError("Fix date cannot be in the future")
            return value
        
        if isinstance(value, datetime):
            if value.date() > datetime.now().date():
                raise ValueError("Fix date cannot be in the future")
            return value.date()
        if isinstance(value, str):
            try:
                # Only accept yyyy-mm-dd format
                dt = datetime.strptime(value, "%Y-%m-%d")
                if dt > datetime.now():
                    raise ValueError("Fix date cannot be in the future")
                return dt.date()
            except Exception:
                raise ValueError("Invalid fix date format. Must be yyyy-mm-dd.")
            
        raise ValueError("Invalid fix date. Must be a valid date in yyyy-mm-dd format.")


    class Config:
        extra = "forbid"
