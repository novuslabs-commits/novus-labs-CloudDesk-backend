from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.agent import Agent
from app.models.ticket import Ticket
from app.schemas.agent import AgentCreate, AgentResponse
from app.services.auth import hash_password, get_current_agent, require_admin
from pydantic import BaseModel
router = APIRouter(prefix="/agents", tags=["agents"])

@router.post("", response_model=AgentResponse, status_code=201)
def create_agent(
    data: AgentCreate,
    db: Session = Depends(get_db),
    _: Agent = Depends(require_admin)
):
    if db.query(Agent).filter(Agent.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    agent = Agent(
        name=data.name,
        email=data.email,
        hashed_password=hash_password(data.password),
        role=data.role,
        team=data.team
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent

@router.get("", response_model=list[AgentResponse])
def list_agents(
    db: Session = Depends(get_db),
    _: Agent = Depends(get_current_agent)
):
    return db.query(Agent).filter(Agent.is_active == True).all()


class AvailabilityUpdate(BaseModel):
    availability: str  # "free" or "busy"

@router.patch("/{agent_id}/availability", response_model=AgentResponse)
def update_availability(
    agent_id: int,
    data: AvailabilityUpdate,
    db: Session = Depends(get_db),
    current: Agent = Depends(get_current_agent)
):
    if data.availability not in ["free", "busy"]:
        raise HTTPException(status_code=400, detail="Availability must be 'free' or 'busy'")

    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent.availability = data.availability
    db.commit()
    db.refresh(agent)
    return agent

@router.get("/workload")
def agent_workload(
    db: Session = Depends(get_db),
    _: Agent = Depends(get_current_agent)
):
    agents = db.query(Agent).filter(Agent.is_active == True).all()
    result = []
    for agent in agents:
        open_tickets = db.query(Ticket).filter(
            Ticket.assigned_agent_id == agent.id,
            Ticket.status.in_(["open", "in_progress"])
        ).count()
        result.append({
            "agent_id": agent.id,
            "name": agent.name,
            "team": agent.team,
            "open_tickets": open_tickets
        })
    return result

@router.get("/me", response_model=AgentResponse)
def get_me(agent: Agent = Depends(get_current_agent)):
    return agent

@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    _: Agent = Depends(get_current_agent)
):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent