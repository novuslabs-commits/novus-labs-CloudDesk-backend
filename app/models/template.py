from sqlalchemy import Column, Integer, String, Text, DateTime, Float ,ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Template(Base):
    __tablename__ = "templates"

    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String(200), nullable=False)
    body        = Column(Text, nullable=False)
    intent      = Column(String(50), nullable=False)    # which intent this template is for
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    suggestions = relationship("TemplateSuggestion", back_populates="template")


class TemplateSuggestion(Base):
    __tablename__ = "template_suggestions"

    id          = Column(Integer, primary_key=True, index=True)
    ticket_id   = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=False)
    similarity  = Column(Float, nullable=False)

    ticket      = relationship("Ticket", back_populates="templates_suggested")
    template    = relationship("Template", back_populates="suggestions")