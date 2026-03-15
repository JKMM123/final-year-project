from pydantic import BaseModel, Field
from typing import Optional


class SearchPackagesRequestQuery(BaseModel):
    amperage: Optional[int] = Field(None, description="Filter by package amperage")
    page: Optional[int] = Field(1, ge=1, description="Page number for pagination")
    limit: Optional[int] = Field(10, ge=1, le=100, description="Number of packages per page")

    class Config:
        extra = "forbid"
