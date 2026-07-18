from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.template import Template
from app.services.auth import get_current_agent
from app.models.agent import Agent

router = APIRouter(prefix="/templates", tags=["templates"])

@router.get("")
def list_templates(
    intent: str = None,
    db: Session = Depends(get_db),
    _: Agent = Depends(get_current_agent)
):
    query = db.query(Template)
    if intent:
        query = query.filter(Template.intent == intent)
    return query.order_by(Template.intent, Template.title).all()