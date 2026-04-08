from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import date, datetime
from typing import Optional, List
import re


class SearchFixesRequestBody(BaseModel):
    page: int = Field(
        default=1,
        ge=1,
        description="Page number for pagination",
        example=1
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of items per page",
        example=10
    )
    query: Optional[str] = Field(None, description="Search query for fix description")
    fix_date: Optional[date] = Field(None, description="Filter fixes from this date")

    @field_validator('query')
    def validate_query(cls, v):
        if v is None:
            return v
        
        v = v.strip()
        if not v:
            return v

        # Allow Arabic, English, numbers, spaces, _ and -
        if not re.fullmatch(r"^[\u0600-\u06FFa-zA-Z0-9_-]+(\s[\u0600-\u06FFa-zA-Z0-9_-]+)*$", v):
            raise ValueError("Invalid query format. Only Arabic, English letters, numbers, spaces, _ and - are allowed.")
        return v


    @field_validator('fix_date')
    def validate_fix_date_to(cls, value):
        if isinstance(value, date):
            return value
        
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            try:
                # Only accept yyyy-mm-dd format
                dt = datetime.strptime(value, "%Y-%m-%d")
                return dt.date()
            
            except Exception:
                raise ValueError("Invalid fix date format. Must be yyyy-mm-dd.")
            
        raise ValueError("Invalid fix date. Must be a valid date in yyyy-mm-dd format.")


    class Config:
        extra = "forbid"
        str_strip_whitespace = True
