from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.feedback import Feedback
from app.models.ticket import Ticket
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.services.auth import get_current_agent
from app.models.agent import Agent

router = APIRouter(prefix="/feedback", tags=["feedback"])

VALID_INTENTS = [
    "billing", "technical", "feature_request",
    "complaint", "refund", "account_access", "general"
]

@router.post("", response_model=FeedbackResponse, status_code=201)
def submit_feedback(
    data: FeedbackCreate,
    db: Session = Depends(get_db),
    agent: Agent = Depends(get_current_agent)
):
    ticket = db.query(Ticket).filter(Ticket.id == data.ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if data.correct_intent not in VALID_INTENTS:
        raise HTTPException(status_code=400, detail="Invalid intent")
    if db.query(Feedback).filter(Feedback.ticket_id == data.ticket_id).first():
        raise HTTPException(status_code=400, detail="Feedback already submitted for this ticket")

    feedback = Feedback(
        ticket_id=data.ticket_id,
        predicted_intent=ticket.intent,
        correct_intent=data.correct_intent,
        agent_id=agent.id
    )
    db.add(feedback)
     #clear since human checked it
    ticket.needs_review=False
    db.commit()
    db.refresh(feedback)
    return feedback

@router.get("", response_model=list[FeedbackResponse])
def list_feedback(
    db: Session = Depends(get_db),
    _: Agent = Depends(get_current_agent)
):
    return db.query(Feedback).order_by(Feedback.created_at.desc()).all()

@router.get("/count")
def feedback_count(
    db: Session = Depends(get_db),
    _: Agent = Depends(get_current_agent)
):
    total = db.query(Feedback).count()
    return {"total_feedback": total, "ready_for_retraining": total >= 50}