from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from uuid import UUID

class GetStatementSchema(BaseModel):
    year: int = Field(..., description="The year for which the statement is requested.")
    meter_id: UUID = Field(..., description="The ID of the meter for which the statement is requested.")

    @field_validator("year")
    def validate_year(cls, value):
        current_year = datetime.now().year
        if value < 2000 or value > current_year:
            raise ValueError(f"Year must be between 2000 and {current_year}.")
        return value

