from sqlalchemy.orm import Session
from app.models.agent import Agent
from app.models.ticket import Ticket

INTENT_TEAM_MAP = {
    "billing":          "Billing",
    "technical":        "Engineering",
    "feature_request":  "Product",
    "complaint":        "Customer Success",
    "refund":           "Billing",
    "account_access":   "Engineering",
    "general":          "Customer Success"
}

def get_assigned_team(intent: str) -> str:
    return INTENT_TEAM_MAP.get(intent, "Customer Success")

def get_best_agent(team: str, db: Session) -> Agent | None:
    agents = db.query(Agent).filter(
        Agent.team == team,
        Agent.is_active == True,
        Agent.availability == "free"  # only assign to free agents
    ).all()

    if not agents:
        # fallback — no free agents, assign to least busy one anyway
        agents = db.query(Agent).filter(
            Agent.team == team,
            Agent.is_active == True
        ).all()

    if not agents:
        return None

    def open_ticket_count(agent: Agent) -> int:
        return db.query(Ticket).filter(
            Ticket.assigned_agent_id == agent.id,
            Ticket.status.in_(["open", "in_progress"])
        ).count()

    return min(agents, key=open_ticket_count)