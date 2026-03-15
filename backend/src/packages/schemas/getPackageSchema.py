from pydantic import BaseModel, Field
from uuid import UUID

class GetPackageRequestPath(BaseModel):
    package_id: UUID = Field(..., description="The ID of the package to retrieve")

    class Config:
        extra = "forbid"
