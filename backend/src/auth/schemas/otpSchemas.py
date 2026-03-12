from pydantic import BaseModel, Field, field_validator
import re

class SendOTPQueryParamsRequestBody(BaseModel):
    phone_number: str = Field(..., description="The phone number to send the OTP to")

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



class VerifyOTPQueryParamsRequestBody(BaseModel):
    phone_number: str = Field(..., description="The phone number associated with the OTP")
    otp: str = Field(..., description="The one-time password to verify")

    @field_validator('phone_number')
    def validate_lebanese_phone(cls, v):
        if v is None:
            return v
        
        pattern = r"^(03|70|71|76|78|79|81)\d{6}$"
        if not re.fullmatch(pattern, v):
            raise ValueError("Invalid Lebanese phone number format")
        return v
    
    @field_validator('otp')
    def validate_otp(cls, v):
        if v is None:
            return v
        
        if not re.fullmatch(r"^\d{4}$", v):
            raise ValueError("OTP must be a 4-digit number")
        return v
    
    class Config:
        extra = "forbid"

