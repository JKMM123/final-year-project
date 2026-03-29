from pydantic import BaseModel


class DeletePaymentSchema(BaseModel):
    message: str = "Payment deleted successfully"
