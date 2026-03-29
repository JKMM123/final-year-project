from pydantic import BaseModel, Field
from uuid import UUID

class GetPaymentSchema(BaseModel):
    payment_id: UUID = Field(..., description="ID of the payment")

    class Config:
        extra = 'forbid'


class GetPaymentsByBillSchema(BaseModel):
    bill_id: UUID = Field(..., description="ID of the bill")

    class Config:
        extra = 'forbid'
        