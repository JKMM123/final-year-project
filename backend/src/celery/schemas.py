from pydantic import BaseModel, Field   
from uuid import UUID


class CeleryTaskStatusRequestPath(BaseModel):
    task_id: UUID = Field(..., description="The ID of the Celery task")

    class Config:
        extra = "forbid"    
