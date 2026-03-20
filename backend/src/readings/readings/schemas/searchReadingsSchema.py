from uuid import UUID 
from datetime import datetime, date
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import re

class SearchReadingsRequestBody(BaseModel):
    query: Optional[str] = Field(None, description="Filter readings by customer name or phone number")
    status: Optional[List[str]] = Field(None, description="Filter readings by status")
    reading_date: str = Field(..., description="Filter readings by date")
    area_ids : Optional[List[UUID]] = Field(None, description="Filter readings by area IDs")
    page: Optional[int] = Field(1, ge=1, description="Page number for pagination")
    limit: Optional[int] = Field(10, ge=1, le=30, description="Number of readings per page")

    @field_validator('query')
    def validate_query(cls, v):
        v = v.strip()
        if not v:
            return v
            
        # Allow Arabic, English, numbers, spaces, _ and -
        if not re.fullmatch(r"^[\u0600-\u06FFa-zA-Z0-9_-]+(\s[\u0600-\u06FFa-zA-Z0-9_-]+)*$", v):
            raise ValueError("Invalid query format. Only Arabic, English letters, numbers, spaces, _ and - are allowed.")
        
        return v.strip()

    @field_validator('status')
    def validate_status(cls, value):
        allowed_statuses = ['pending', 'verified']
        for status in value or []:
            if status not in allowed_statuses:
                raise ValueError(f"Invalid status: {status}. Allowed values are {allowed_statuses}.")
        return value

    @field_validator('reading_date')
    def validate_reading_date(cls, value):
        if not value:
            return value
        try:
            # Validate yyyy-mm format
            datetime.strptime(value, "%Y-%m")
        except ValueError:
            raise ValueError("Invalid reading date format. Must be yyyy-mm.")
        return value
    class Config:
        extra = "forbid"
