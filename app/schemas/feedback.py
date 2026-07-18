from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FeedbackCreate(BaseModel):
    ticket_id: int
    correct_intent: str

class FeedbackResponse(BaseModel):
    id: int
    ticket_id: int
    predicted_intent: str
    correct_intent: str
    agent_id: int
    created_at: datetime

    model_config = {"from_attributes": True }