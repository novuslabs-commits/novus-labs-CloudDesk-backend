from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.ticket import Ticket, TicketStatus
from app.models.feedback import Feedback
from app.models.agent import Agent
from app.services.auth import get_current_agent
from datetime import datetime, timedelta

router = APIRouter(prefix="/metrics", tags=["metrics"])

@router.get("")
def get_metrics(
    db: Session = Depends(get_db),
    _: Agent = Depends(get_current_agent)
):
    total_tickets = db.query(Ticket).count()
    open_tickets = db.query(Ticket).filter(Ticket.status == TicketStatus.open).count()
    resolved_tickets = db.query(Ticket).filter(Ticket.status == TicketStatus.resolved).count()
    needs_review = db.query(Ticket).filter(Ticket.needs_review == True).count()
    total_feedback = db.query(Feedback).count()

    # Average model confidence across all classified tickets
    avg_confidence = db.query(func.avg(Ticket.confidence)).filter(Ticket.confidence.isnot(None)).scalar()
    avg_confidence = round(avg_confidence * 100, 2) if avg_confidence else None

    # intent / urgency / sentiment distributions (unchanged)
    intent_dist = db.query(Ticket.intent, func.count(Ticket.id).label("count")).group_by(Ticket.intent).all()
    urgency_dist = db.query(Ticket.urgency, func.count(Ticket.id).label("count")).group_by(Ticket.urgency).all()
    sentiment_dist = db.query(Ticket.sentiment, func.count(Ticket.id).label("count")).group_by(Ticket.sentiment).all()

    # Feedback-based accuracy (ground truth from human corrections)
    correct_predictions = db.query(Feedback).filter(Feedback.predicted_intent == Feedback.correct_intent).count()
    feedback_accuracy = round(correct_predictions / total_feedback * 100, 2) if total_feedback > 0 else None

    # agent workload (unchanged)
    agents = db.query(Agent).filter(Agent.is_active == True).all()
    agent_workload = []
    for agent in agents:
        open_count = db.query(Ticket).filter(
            Ticket.assigned_agent_id == agent.id,
            Ticket.status.in_(["open", "in_progress"])
        ).count()
        agent_workload.append({
            "agent_id": agent.id,
            "name": agent.name,
            "team": agent.team,
            "open_tickets": open_count
        })

    return {
        "total_tickets": total_tickets,
        "open_tickets": open_tickets,
        "resolved_tickets": resolved_tickets,
        "needs_review": needs_review,
        "total_feedback": total_feedback,
        "avg_confidence": avg_confidence,
        "feedback_accuracy": feedback_accuracy,
        "intent_distribution": {r.intent: r.count for r in intent_dist if r.intent},
        "urgency_distribution": {r.urgency: r.count for r in urgency_dist if r.urgency},
        "sentiment_distribution": {r.sentiment: r.count for r in sentiment_dist if r.sentiment},
        "agent_workload": agent_workload
    }

@router.get("/trend")
def get_ticket_trend(
    db: Session = Depends(get_db),
    _: Agent = Depends(get_current_agent)
):
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    results = db.query(
        func.date(Ticket.created_at).label("date"),
        func.count(Ticket.id).label("count")
    ).filter(
        Ticket.created_at >= thirty_days_ago
    ).group_by(
        func.date(Ticket.created_at)
    ).order_by(
        func.date(Ticket.created_at)
    ).all()

    # fill in missing days with 0 so the line doesn't skip gaps
    date_counts = {str(r.date): r.count for r in results}
    trend = []
    for i in range(30, -1, -1):
        day = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        trend.append({"date": day, "count": date_counts.get(day, 0)})

    return trend