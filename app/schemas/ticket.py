from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.ticket import TicketStatus, UrgencyLevel

class TicketCreate(BaseModel):
    subject: str = Field(..., min_length=3, max_length=500)
    body: str = Field(..., min_length=10)
    source: str = Field(default="manual")

class RespondRequest(BaseModel):
    template_id: Optional[int] = None
    response_text: str = Field(..., min_length=5)

class ResolveRequest(BaseModel):
    resolution_note: str = Field(..., min_length=5)

class TicketResponse(BaseModel):
    id: int
    subject: str
    body: str
    source: str
    status: TicketStatus
    intent: Optional[str]
    confidence: Optional[float]
    needs_review: bool
    urgency: Optional[UrgencyLevel]
    sentiment: Optional[str]
    sentiment_score: Optional[float]
    assigned_team: Optional[str]
    assigned_agent_id: Optional[int]
    initial_response_sent_at: Optional[datetime]
    initial_template_id: Optional[int]
    initial_response_text: Optional[str]
    resolved_by_agent_id: Optional[int]
    resolution_note: Optional[str]
    resolution_sent_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    resolved_at: Optional[datetime]

    model_config = {"from_attributes": True}

class TicketStatusUpdate(BaseModel):
    status: TicketStatus

class TicketListResponse(BaseModel):
    tickets: list[TicketResponse]
    total: int
    page: int
    page_size: int