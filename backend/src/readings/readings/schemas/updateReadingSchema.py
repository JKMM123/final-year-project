from pydantic import BaseModel, Field, field_validator
from enum import Enum
from datetime import datetime


class UpdateReadingRequestBody(BaseModel):
    current_reading: float = Field(..., description="Current reading amount", ge=0)
    status: str = Field(..., description="Status of the reading ('active', 'inactive')")

    class Config:
        extra = "forbid"


class VerifyAllReadings(BaseModel):
    confirm: bool = Field(False, description="Confirmation to verify all readings")
    reading_date: str = Field(..., description="Date of the readings to verify in YYYY-MM-DD format")

    @field_validator('reading_date')
    def validate_reading_date(cls, value):
        try:
            # Validate yyyy-mm format
            datetime.strptime(value, "%Y-%m")
        except ValueError:
            raise ValueError("Invalid reading date format. Must be yyyy-mm.")
        return value

    class Config:
        extra = "forbid"



class ReadingStatusUpdate(str, Enum):
    system = "system"
    admin = "admin"
    

    @classmethod
    def can_update_status(cls, user_role: str) -> bool:
        user_role = user_role.lower().strip()
        return user_role in [cls.admin.value, cls.system.value]

    
