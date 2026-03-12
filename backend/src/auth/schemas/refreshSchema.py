from pydantic import BaseModel, Field
from typing import Optional



class RefreshSchema(BaseModel):
    """
    Schema for the user refresh token.
    """    
    
    refresh_token: str = Field(
        ..., 
        min_length=10,
        max_length=5000,
        description="Refresh token for authentication")
    
    