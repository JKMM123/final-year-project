from pydantic import BaseModel, Field, model_validator
from uuid import UUID


class GetBillRequestPath(BaseModel):
    bill_id: UUID = Field(..., description="Unique identifier for the bill")

    class Config:
        extra = "forbid"


class ShowBillRequestPath(BaseModel):
    bill_number: int = Field(..., description="Unique identifier for the bill")

    class Config:
        extra = "forbid"


