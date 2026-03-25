from typing import List
from pydantic import BaseModel, Field
from typing import Any  


class FieldError(BaseModel):
    field: str = Field(..., description="Field name that caused the error")
    message: str = Field(..., description="Error message for the field")


class RequestErrors(BaseModel):
    message: str = Field(..., description="General error message")
    error: str = Field(..., description="Error type")
    fieldErrors: Any = Field(
        default_factory=list, 
        description="List of field-specific errors, if any"
    )
    status: int = Field(..., description="HTTP status code")
    timeStamp: str = Field(..., description="Timestamp of the error")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Error message",
                "error": "Error type",
                "fieldErrors": [
                    {
                        "field": "Field name",
                        "message": "Field error message"
                    }
                ],
                "status": "status code",
                "timeStamp": "2024-02-04T12:00:00.000Z"
            }
        }


class RequestResponse(BaseModel):
    message: str = Field(..., description="Response message")
    data: Any = Field(..., description="Response data")
    status: int = Field(..., description="HTTP status code")
    timeStamp: str = Field(..., description="Timestamp of the response")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "message",
                "data": {
                        "exmaple": "data"   
                    }
                ,
                "status": 200,
                "timeStamp": "2024-02-04T12:00:00.000Z"
            }
        }