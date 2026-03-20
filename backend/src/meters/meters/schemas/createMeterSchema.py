from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from uuid import UUID
import re


class CreateMeterRequestBody(BaseModel):
    customer_full_name: str = Field(..., description="The full name of the customer associated with the meter")
    customer_phone_number: str = Field(..., description="The phone number of the customer associated with the meter")
    area_id: UUID = Field(..., description="The ID of the area where the meter is installed")
    address: Optional[str] = Field(..., description="The address where the meter is installed")
    initial_reading: Optional[float] = Field(None, description="The initial reading of the meter at the time of installation", ge= 0)
    package_id: UUID = Field(..., description="The ID of the package associated with the meter")
    package_type: str = Field(..., description="The type of package associated with the meter")

    @field_validator("customer_full_name")
    def validate_customer_full_name(cls, value: str) -> str:
        if value is None or value.strip() == "":
            raise ValueError("Customer full name cannot be empty")
        # Allow Arabic, English, numbers, spaces, _ and -
        if not re.fullmatch(r"^[\u0600-\u06FFa-zA-Z0-9_-]+(\s[\u0600-\u06FFa-zA-Z0-9_-]+)*$", value):
            raise ValueError("Invalid customer full name format")
        return value.strip()
    

    @field_validator("address")
    def validate_address(cls, value: str) -> str:
        if value is None:
            return value
        if not re.match(r"^[\u0600-\u06FFa-zA-Z0-9\s._-]+$", value):
            raise ValueError("Address can only contain Arabic, English letters, numbers, spaces, ., _, and - characters")
        return value.strip()
    
    @field_validator("package_type")
    def validate_package_type(cls, value: str) -> str:
        allowed_types = ["usage", "fixed"]
        if value not in allowed_types:
            raise ValueError(f"Package type must be one of the following: {', '.join(allowed_types)}")
        return value.strip()
    
    @field_validator("customer_phone_number")
    def validate_lebanese_phone(cls, v):
        if v is None:
            return v
        
        pattern = r"^(03|70|71|76|78|79|81)\d{6}$"
        if not re.fullmatch(pattern, v):
            raise ValueError("Invalid Lebanese phone number format")
        return v
    
    @model_validator(mode='after')
    def validate_initial_reading_based_on_package_type(self):
        package_type = self.package_type
        initial_reading = self.initial_reading
        
        if package_type == "fixed":
            if initial_reading is not None:
                raise ValueError("Initial reading must be None for fixed package type")
            # Set to None explicitly
            self.initial_reading = None
        elif package_type == "usage":
            if initial_reading is None:
                raise ValueError("Initial reading is required for usage package type")
            if initial_reading < 0:
                raise ValueError("Initial reading must be greater than or equal to 0")
        
        return self

    class Config:
        extra = "forbid"
        