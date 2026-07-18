from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Feedback(Base):
    __tablename__ = "feedback"

    id              = Column(Integer, primary_key=True, index=True)
    ticket_id       = Column(Integer, ForeignKey("tickets.id"), unique=True, nullable=False)
    predicted_intent = Column(String(50), nullable=False)
    correct_intent  = Column(String(50), nullable=False)
    agent_id        = Column(Integer, ForeignKey("agents.id"), nullable=False)
    note            = Column(Text, nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    ticket          = relationship("Ticket", back_populates="feedback")