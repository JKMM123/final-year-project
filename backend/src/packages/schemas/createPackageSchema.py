from pydantic import BaseModel, Field


class CreatePackageRequestBody(BaseModel):
    amperage: int = Field(..., description="The amperage of the package", gt=0)
    activation_fee: float = Field(..., description="The activation fee for the package", gt=0)
    fixed_fee: float = Field(..., description="The fixed fee for the package", gt=0)

    class Config:
        extra = "forbid"
