from pydantic import BaseModel, Field
from uuid import UUID


class DeleteUserRequestPath(BaseModel):
    user_id: UUID = Field(..., description="The ID of the user to delete")
    class Config:
        extra = "forbid"
