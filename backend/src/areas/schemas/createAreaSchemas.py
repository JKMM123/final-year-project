from pydantic import BaseModel, Field, field_validator
import re

class CreateAreaRequestBody(BaseModel):
    area_name: str = Field(..., description="Name of the area")
    elevation: float = Field(..., description="Elevation of the area in meters", ge=0)


    @field_validator("area_name")
    def validate_area_name(cls, v):
        if v is None or v.strip() == "":
            raise ValueError("Area name cannot be empty")
        if not re.fullmatch(r"^[\u0600-\u06FFa-zA-Z0-9_-]+(\s[\u0600-\u06FFa-zA-Z0-9_-]+)*$", v):
            raise ValueError("Invalid area name format")
        return v
    

    class Config:
        extra = "forbid"
