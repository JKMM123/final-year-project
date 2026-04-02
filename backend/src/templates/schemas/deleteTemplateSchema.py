from pydantic import BaseModel, Field
from uuid import UUID


class DeleteTemplateRequestPath(BaseModel):
    template_id: UUID = Field(..., description="Template ID")

    class Config:
        extra = "forbid"
