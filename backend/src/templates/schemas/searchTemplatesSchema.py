from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re


class SearchTemplatesRequestQuery(BaseModel):
    query: Optional[str] = Field(None, description="Search term for template names or descriptions")
    page: Optional[int] = Field(1, ge=1, le=100, description="Page number for pagination")
    limit: Optional[int] = Field(10, ge=1, le=50, description="Number of templates per page")

    @field_validator("query")
    def validate_query(cls, v):
        if v is None or not v.strip():
            return v
        
        # Allow Arabic, English, numbers, spaces, underscore, and hyphen
        if not re.fullmatch(r"^[\u0600-\u06FFa-zA-Z0-9_-]+(\s[\u0600-\u06FFa-zA-Z0-9_-]+)*$", v):
            raise ValueError("Invalid query format. Only Arabic, English letters, numbers, spaces, _ and - are allowed.")
        return v.strip()


    class Config:
        extra = "forbid"
        str_strip_whitespace = True

        
