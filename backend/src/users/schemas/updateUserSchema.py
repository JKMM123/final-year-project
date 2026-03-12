from pydantic import BaseModel, Field, field_validator
import re
from uuid import UUID


class UpdateUserRequestPath(BaseModel):
    user_id: UUID = Field(..., description="The ID of the user to update")

    class Config:
        extra = "forbid"


class UpdateUserRequestBody(BaseModel):
    username: str = Field(..., description="The username of the user")
    phone_number: str = Field(..., description="The phone number of the user")
    role: str = Field(..., description="The role of the user, e.g., 'admin', 'user'")


    @field_validator("phone_number")
    def validate_phone_number(cls, v):
        pattern = r"^(03|70|71|76|78|79|81)\d{6}$"
        if not re.fullmatch(pattern, v):
            raise ValueError("Invalid Lebanese phone number format")
        return v


    @field_validator("role")
    def validate_role(cls, v):
        if v not in ["system", "admin", "user"]:
            raise ValueError("Invalid role. Role must be either 'system', 'admin' or 'user'.")
        return v
    
    @field_validator("username")
    def validate_username(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Username cannot be empty")
        # Allow Arabic, English, numbers, spaces, _ and -
        if not re.fullmatch(r"^[\u0600-\u06FFa-zA-Z0-9_-]+(\s[\u0600-\u06FFa-zA-Z0-9_-]+)*$", v):
            raise ValueError("Invalid username format. Only Arabic, English letters, numbers, spaces, _ and - are allowed.")
        return v
    
    

    class Config:
        extra = "forbid"
