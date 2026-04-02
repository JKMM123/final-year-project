from pydantic import BaseModel, Field, field_validator
import re

class CreateSessionRequestBody(BaseModel):
    name: str = Field(..., description="The name of the session to create", min_length=1, max_length=100)
    phone_number: str = Field(..., description="The phone number of the user")

    @field_validator('name')
    def validate_name(cls, value: str) -> str:
        if value is None or value.strip() == "":
            raise ValueError("Name cannot be empty")
        # Allow Arabic, English, numbers, spaces, _ and -
        if not re.fullmatch(r"^[\u0600-\u06FFa-zA-Z0-9_-]+(\s[\u0600-\u06FFa-zA-Z0-9_-]+)*$", value):
            raise ValueError("Invalid name format")
        return value.strip()


    @field_validator('phone_number')
    def validate_lebanese_phone(cls, v):
        if v is None:
            return v
        
        pattern = r"^(03|70|71|76|78|79|81)\d{6}$"
        if not re.fullmatch(pattern, v):
            raise ValueError("Invalid Lebanese phone number format")
        return v

    class Config:
        extra = "forbid"