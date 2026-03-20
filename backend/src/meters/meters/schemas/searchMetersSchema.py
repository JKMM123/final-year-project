from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from typing import Optional, List
import re


class SearchMetersRequestBody(BaseModel):
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
    query: Optional[str] = Field(None, description="Search query for meter details")
    area_ids: Optional[List[UUID]] = Field(None, description="Filter by area IDs")
    package_ids: Optional[List[UUID]] = Field(
        None,
        description="Filter by package ID"
    )
    package_type: Optional[str] = Field(
        None,
        description="Filter by package type"
    )
    status: Optional[List[str]] = Field(
        None,
        description="Filter by meter status"
    )
    reading_date: Optional[str] = Field(None, description="Filter by reading date")

    @field_validator('query')
    def validate_query(cls, v):
        v = v.strip()
        if not v:
            return v

        # Allow Arabic, English, numbers, spaces, _ and -
        if not re.fullmatch(r"^[\u0600-\u06FFa-zA-Z0-9_-]+(\s[\u0600-\u06FFa-zA-Z0-9_-]+)*$", v):
            raise ValueError("Invalid query format. Only Arabic, English letters, numbers, spaces, _ and - are allowed.")
        return v

    @field_validator('package_type')
    def validate_package_type(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            allowed_types = ["usage", "fixed"]
            if value not in allowed_types:
                raise ValueError(f"Package type must be one of the following: {', '.join(allowed_types)}")
        return value.strip() if value else None

    @field_validator('status')
    def validate_status(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is not None:
            allowed_statuses = ["active", "inactive", "awaiting_reading", "have_reading"]
            for status in value:
                if status not in allowed_statuses:
                    raise ValueError(f"Status must be one of the following: {', '.join(allowed_statuses)}")
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



    




