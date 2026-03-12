from pydantic import BaseModel, Field, field_validator
import re
from uuid import UUID


class LoginRequestBody(BaseModel):
    username_or_phone: str = Field(...)
    password: str = Field(...)
    device_id: UUID = Field(...)


    @field_validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        return v



    class Config:
        extra = "forbid"  
