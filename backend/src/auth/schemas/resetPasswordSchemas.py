import re
from pydantic import BaseModel, Field, field_validator


class ResetPasswordRequestBody(BaseModel):
    phone_number: str = Field(..., description="The phone number associated with the account")
    new_password: str = Field(..., description="The new password for the user account")
    reset_token: str = Field(..., description="The token for resetting the password", min_length=32, max_length=32)

    @field_validator('phone_number')
    def validate_lebanese_phone(cls, v):
        if v is None:
            return v
        
        pattern = r"^(03|70|71|76|78|79|81)\d{6}$"
        if not re.fullmatch(pattern, v):
            raise ValueError("Invalid Lebanese phone number format")
        return v
    
    @field_validator('new_password')
    def validate_password(cls, v):
        if v is None:
            return v
        
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

