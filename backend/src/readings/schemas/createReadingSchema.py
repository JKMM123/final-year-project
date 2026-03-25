from pydantic import BaseModel, Field, model_validator
from uuid import UUID
from datetime import datetime
from typing import Optional
from src.readings.exceptions.exceptions import InvalidReadingValueException


class CreateReadingRequestBody(BaseModel):
    meter_id: UUID = Field(..., description="The ID of the meter")
    current_reading: float = Field(..., description="Current reading amount", ge=0)

    class Config:
        extra = "forbid"
