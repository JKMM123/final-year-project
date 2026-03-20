from pydantic import BaseModel, Field, field_validator, model_validator
import re
from typing import Optional
from uuid import UUID
 
class MeterFileUploadRow(BaseModel):
    customer_full_name: str = Field(..., description="Name of the customer", min_length=1, max_length=50)
    customer_phone_number: str = Field(..., description="Phone number of the customer")
    area_id: UUID = Field(..., description="ID of the area")
    address: str = Field(..., description="Address of the customer", min_length=1, max_length=100)
    package_id: UUID = Field(..., description="ID of the package")
    package_type: str = Field(..., description="Type of the package", min_length=1, max_length=50)
    initial_reading: Optional[float] = Field(None, description="Initial reading of the meter", ge= 0.0, le=9999999.9)

    @field_validator("package_type")
    def validate_package_type(cls, v):
        allowed_types = ["fixed", "usage"]
        if v not in allowed_types:
            raise ValueError(f"Package type must be one of {allowed_types}")
        return v.lower()

    @field_validator("customer_full_name")
    def validate_customer_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Customer full name cannot be empty")
        
        # Allow Arabic, English, numbers, spaces, _ and -
        if not re.fullmatch(r"^[\u0600-\u06FFa-zA-Z0-9_-]+(\s[\u0600-\u06FFa-zA-Z0-9_-]+)*$", v):
            raise ValueError("Invalid customer full name format. Only Arabic, English letters, numbers, spaces, _ and - are allowed.")
        return v.strip()

    @field_validator("customer_phone_number")
    def validate_lebanese_phone(cls, v):
        if v is None:
            return v
        
        pattern = r"^(03|70|71|76|78|79|81)\d{6}$"
        if not re.fullmatch(pattern, v):
            raise ValueError("Invalid Lebanese phone number format")
        return v

    @field_validator("address") 
    def validate_address(cls, v):
        if not v or not v.strip():
            raise ValueError("Address cannot be empty")
        
        # Allow Arabic, English, numbers, spaces, ., _, and - characters
        if not re.fullmatch(r"^[\u0600-\u06FFa-zA-Z0-9\s._-]+$", v):
            raise ValueError("Address can only contain Arabic, English letters, numbers, spaces, ., _, and - characters")
        return v.strip()
    
    @model_validator(mode='after')
    def validate_initial_reading_based_on_package_type(self):
        package_type = self.package_type
        initial_reading = self.initial_reading
        
        if package_type == "fixed":
            if initial_reading is not None:
                self.initial_reading = None
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
        str_strip_whitespace = True  
        