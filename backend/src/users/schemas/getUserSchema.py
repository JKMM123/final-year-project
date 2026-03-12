from pydantic import BaseModel, Field
from uuid import UUID

class GetUserRequestPath(BaseModel):
    user_id: UUID = Field(..., description="The ID of the user to retrieve")

    class Config:
        extra = "forbid"