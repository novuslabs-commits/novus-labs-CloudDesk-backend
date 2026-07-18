from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class AgentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str = Field(default="agent")
    team: Optional[str] = None

class AgentResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    team: Optional[str]
    is_active: bool
    availability: str
    created_at: datetime

    model_config = {"from_attributes": True}

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    agent: AgentResponse