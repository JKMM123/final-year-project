from typing import Optional
from pydantic import BaseModel, Field, field_validator
import re


class SearchAreasRequestParams(BaseModel):
    query: Optional[str] = Field(
        default=None,
        description="Search term for area names",
        example="John Doe"
    )
    page: int = Field(
        default=1,
        ge=1,
        le=100,
        description="Page number for pagination",
        example=1
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Number of items per page",
        example=10
    )

    @field_validator('query')
    def validate_query(cls, v):
        if v is None or v.strip() == "":
            return v
        # Allow Arabic, English, numbers, spaces, _ and -
        if not re.fullmatch(r"^[\u0600-\u06FFa-zA-Z0-9_-]+(\s[\u0600-\u06FFa-zA-Z0-9_-]+)*$", v):
            raise ValueError("Invalid search term format")
        return v


    class Config:
        extra = "forbid"