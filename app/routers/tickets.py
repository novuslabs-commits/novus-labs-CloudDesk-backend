from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.ticket import Ticket, TicketStatus
from app.models.template import TemplateSuggestion, Template
from app.schemas.ticket import (
    TicketCreate, TicketResponse, TicketStatusUpdate, TicketListResponse,
    RespondRequest, ResolveRequest
)
from app.services.classifier import classifier
from app.services.urgency import score_urgency
from app.services.sentiment import analyze_sentiment
from app.services.router import get_assigned_team, get_best_agent
from app.services.template_matcher import template_matcher
from app.services.auth import get_current_agent
from app.models.agent import Agent
from datetime import datetime
from google import genai
from app.config import get_settings

router = APIRouter(prefix="/tickets", tags=["tickets"])

async def process_ticket(ticket: Ticket, db: Session):
    """Classify, score, route and suggest templates for a ticket."""
    result = await run_in_threadpool(classifier.classify, f"{ticket.subject} {ticket.body}")
    sentiment = analyze_sentiment(ticket.body)
    urgency = score_urgency(ticket.body)
    team = get_assigned_team(result["intent"])
    agent = get_best_agent(team, db)
    templates = template_matcher.match(ticket.body, result["intent"])

    ticket.intent = result["intent"]
    ticket.confidence = result["confidence"]
    ticket.needs_review = result["needs_review"]
    ticket.urgency = urgency
    ticket.sentiment = sentiment["label"]
    ticket.sentiment_score = sentiment["score"]
    ticket.assigned_team = team
    ticket.assigned_agent_id = agent.id if agent else None

    for t in templates:
        db.add(TemplateSuggestion(
            ticket_id=ticket.id,
            template_id=t["template_id"],
            similarity=t["similarity"]
        ))

@router.post("", response_model=TicketResponse, status_code=201)
async def create_ticket(
    data: TicketCreate,
    db: Session = Depends(get_db),
    _: Agent = Depends(get_current_agent)
):
    ticket = Ticket(subject=data.subject, body=data.body, source=data.source)
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    await process_ticket(ticket, db)
    db.commit()
    db.refresh(ticket)
    return ticket

@router.get("", response_model=TicketListResponse)
def list_tickets(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: TicketStatus = Query(default=None),
    intent: str = Query(default=None),
    urgency: str = Query(default=None),
    needs_review: bool = Query(default=None),
    db: Session = Depends(get_db),
    _: Agent = Depends(get_current_agent)
):
    query = db.query(Ticket)
    if status:
        query = query.filter(Ticket.status == status)
    if intent:
        query = query.filter(Ticket.intent == intent)
    if urgency:
        query = query.filter(Ticket.urgency == urgency)
    if needs_review is not None:
        query = query.filter(Ticket.needs_review == needs_review)

    total = query.count()
    tickets = query.order_by(Ticket.created_at.desc())\
                   .offset((page - 1) * page_size)\
                   .limit(page_size).all()

    return TicketListResponse(tickets=tickets, total=total, page=page, page_size=page_size)


@router.post("/{ticket_id}/respond", response_model=TicketResponse)
def send_initial_response(
    ticket_id: int,
    data: RespondRequest,
    db: Session = Depends(get_db),
    agent: Agent = Depends(get_current_agent)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.initial_response_sent_at = datetime.utcnow()
    ticket.initial_template_id = data.template_id
    ticket.initial_response_text = data.response_text
    ticket.status = TicketStatus.in_progress

    db.commit()
    db.refresh(ticket)
    return ticket

@router.post("/{ticket_id}/resolve", response_model=TicketResponse)
def resolve_ticket(
    ticket_id: int,
    data: ResolveRequest,
    db: Session = Depends(get_db),
    agent: Agent = Depends(get_current_agent)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.resolved_by_agent_id = agent.id
    ticket.resolution_note = data.resolution_note
    ticket.resolution_sent_at = datetime.utcnow()
    ticket.resolved_at = datetime.utcnow()
    ticket.status = TicketStatus.resolved

    db.commit()
    db.refresh(ticket)
    return ticket

@router.get("/history/list", response_model=TicketListResponse)
def get_ticket_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: TicketStatus = Query(default=None),
    agent_id: int = Query(default=None),
    db: Session = Depends(get_db),
    _: Agent = Depends(get_current_agent)
):
    query = db.query(Ticket).filter(
        Ticket.status.in_([TicketStatus.in_progress, TicketStatus.resolved, TicketStatus.closed])
    )
    if status:
        query = query.filter(Ticket.status == status)
    if agent_id:
        query = query.filter(
            (Ticket.assigned_agent_id == agent_id) | (Ticket.resolved_by_agent_id == agent_id)
        )

    total = query.count()
    tickets = query.order_by(Ticket.updated_at.desc())\
                   .offset((page - 1) * page_size)\
                   .limit(page_size).all()

    return TicketListResponse(tickets=tickets, total=total, page=page, page_size=page_size)

@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    _: Agent = Depends(get_current_agent)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@router.patch("/{ticket_id}/status", response_model=TicketResponse)
def update_status(
    ticket_id: int,
    data: TicketStatusUpdate,
    db: Session = Depends(get_db),
    _: Agent = Depends(get_current_agent)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.status = data.status
    if data.status == TicketStatus.resolved:
        ticket.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(ticket)
    return ticket
@router.patch("/{ticket_id}/assign", response_model=TicketResponse)
def assign_ticket(
    ticket_id: int,
    agent_id: int,
    db: Session = Depends(get_db),
    _: Agent = Depends(get_current_agent)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.assigned_agent_id = agent_id
    db.commit()
    db.refresh(ticket)
    return ticket

@router.get("/{ticket_id}/suggestions")
def get_suggestions(
    ticket_id: int,
    db: Session = Depends(get_db),
    _: Agent = Depends(get_current_agent)
):
    suggestions = db.query(TemplateSuggestion, Template)\
        .join(Template, TemplateSuggestion.template_id == Template.id)\
        .filter(TemplateSuggestion.ticket_id == ticket_id)\
        .order_by(TemplateSuggestion.similarity.desc())\
        .all()
    return [
        {
            "template_id": s.TemplateSuggestion.template_id,
            "title": s.Template.title,
            "body": s.Template.body,
            "similarity": s.TemplateSuggestion.similarity
        }
        for s in suggestions
    ]
@router.post("/{ticket_id}/generate-response")
async def generate_response(
    ticket_id: int,
    db: Session = Depends(get_db),
    _: Agent = Depends(get_current_agent)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    settings = get_settings()

    client = genai.Client(api_key=settings.gemini_api_key)

    prompt = f"""You are a professional customer support agent at a SaaS company called CloudDesk.

A customer has submitted the following support ticket:

Subject: {ticket.subject}

Message: {ticket.body}

Ticket classification:
- Intent: {ticket.intent}
- Urgency: {ticket.urgency}
- Sentiment: {ticket.sentiment}

Write a warm, human, and specific response to this customer.

Strict rules:
- Sound like a real person, not a corporate robot
- Do NOT use phrases like: "we have processed your request", "we have acknowledged your issue", "your ticket has been received", "we are looking into this matter", "thank you for bringing this to our attention", "we apologize for any inconvenience"
- DO use natural human phrases like: "we completely understand", "that's frustrating and we get it", "a relevant expert from our team will reach out to you shortly", "we're on it"
- Address their specific issue directly — reference what they actually said
- Be concise — 3-5 sentences maximum
- If their sentiment is negative or they sound frustrated, lead with genuine empathy first
- If urgency is high, give a clear and specific timeline
- Do not mention AI, classification, or any internal systems
- End with a human sign-off like "— CloudDesk Support" not a formal closing
- Return only the response text, nothing else
"""

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return {"response": response.text}
        except Exception as e:
            if attempt < 2:
                import asyncio
                await asyncio.sleep(15)
            else:
                raise HTTPException(status_code=503, detail="AI response generation temporarily unavailable")