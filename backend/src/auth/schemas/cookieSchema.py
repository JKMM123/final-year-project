from pydantic import BaseModel, Field
from typing import Optional



class CookieSchema(BaseModel):
    """
    Schema for the user cookie.
    """    
    access_token: str = Field(
        ..., 
        min_length=10,
        max_length=5000,
        description="Access token for authentication")
    
    refresh_token: Optional[str] = Field(
        None, 
        min_length=10,
        max_length=5000,
        description="Refresh token for authentication")
    
    class Config:
        extra = "forbid"