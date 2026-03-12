from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re


class SearchUsersRequestQuery(BaseModel):
    query: Optional[str] = Field(None, description="Filter users by username")
    role: Optional[str] = Field(None, description="Filter users by role, e.g., 'admin', 'user'")
    page: Optional[int] = Field(1, ge=1, le=50, description="Page number for pagination")
    limit: Optional[int] = Field(10, ge=1, le=20, description="Number of users per page, max 100")

    @field_validator("role")
    def validate_role(cls, v):
        if v and v not in ["system", "admin", "user"]:
            raise ValueError("Invalid role. Role must be either 'system', 'admin' or 'user'.")
        return v
    
    @field_validator("query")
    def validate_query(cls, v):
        # Allow Arabic, English, numbers, spaces, _ and -
        if v and not re.fullmatch(r"^[\u0600-\u06FFa-zA-Z0-9_-]+(\s[\u0600-\u06FFa-zA-Z0-9_-]+)*$", v):
            raise ValueError("Invalid query format. Only Arabic, English letters, numbers, spaces, _ and - are allowed.")
        return v

    class Config:
        extra = "forbid"