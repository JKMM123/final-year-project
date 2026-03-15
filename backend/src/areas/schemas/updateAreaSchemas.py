from pydantic import BaseModel, Field, field_validator
import re
from uuid import UUID


class UpdateAreaRequestPath(BaseModel):
    area_id: UUID = Field(
        ...,
        description="The unique identifier of the area to update",
        example="123e4567-e89b-12d3-a456-426614174000"
    )


class UpdateAreaRequestBody(BaseModel):
    area_name: str = Field(..., description="Name of the area")
    elevation: float = Field(..., description="Elevation of the area in meters")


    @field_validator("area_name")
    def validate_area_name(cls, v):
        if v is None or v.strip() == "":
            raise ValueError("Area name cannot be empty")
        # Allow Arabic, English, numbers, spaces, _ and -
        if not re.fullmatch(r"^[\u0600-\u06FFa-zA-Z0-9_-]+(\s[\u0600-\u06FFa-zA-Z0-9_-]+)*$", v):
            raise ValueError("Invalid area name format")
        return v
    

    class Config:
        extra = "forbid"
