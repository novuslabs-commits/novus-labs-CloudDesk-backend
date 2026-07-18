from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class TicketStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"

class UrgencyLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"

class Ticket(Base):
    __tablename__ = "tickets"

    id              = Column(Integer, primary_key=True, index=True)
    subject         = Column(String(500), nullable=False)
    body            = Column(Text, nullable=False)
    source          = Column(String(50), default="manual")
    status          = Column(Enum(TicketStatus), default=TicketStatus.open)

    # Classification results
    intent          = Column(String(50), nullable=True)
    confidence      = Column(Float, nullable=True)
    needs_review    = Column(Boolean, default=False)
    urgency         = Column(Enum(UrgencyLevel), nullable=True)
    sentiment       = Column(String(20), nullable=True)
    sentiment_score = Column(Float, nullable=True)

    # Routing
    assigned_team      = Column(String(100), nullable=True)
    assigned_agent_id  = Column(Integer, ForeignKey("agents.id"), nullable=True)

    # NEW — Response lifecycle tracking
    initial_response_sent_at = Column(DateTime(timezone=True), nullable=True)
    initial_template_id      = Column(Integer, ForeignKey("templates.id"), nullable=True)
    initial_response_text    = Column(Text, nullable=True)
    resolved_by_agent_id     = Column(Integer, ForeignKey("agents.id"), nullable=True)
    resolution_note          = Column(Text, nullable=True)
    resolution_sent_at       = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at     = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    assigned_agent  = relationship("Agent", foreign_keys=[assigned_agent_id], back_populates="tickets")
    resolved_by     = relationship("Agent", foreign_keys=[resolved_by_agent_id])
    initial_template = relationship("Template", foreign_keys=[initial_template_id])
    feedback        = relationship("Feedback", back_populates="ticket", uselist=False)
    templates_suggested = relationship("TemplateSuggestion", back_populates="ticket")