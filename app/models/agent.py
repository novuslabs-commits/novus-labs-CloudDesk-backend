from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Agent(Base):
    __tablename__ = "agents"

    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String(100), nullable=False)
    email           = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role            = Column(String(20), default="agent")
    team            = Column(String(100), nullable=True)
    is_active       = Column(Boolean, default=True)
    availability    = Column(String(10), default="free")  # "free" or "busy"
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    tickets = relationship("Ticket", foreign_keys="Ticket.assigned_agent_id", back_populates="assigned_agent")