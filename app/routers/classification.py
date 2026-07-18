from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.classification import ClassifyRequest, ClassificationResponse
from app.services.classifier import classifier
from app.services.urgency import score_urgency
from app.services.sentiment import analyze_sentiment
from app.services.router import get_assigned_team
from app.services.template_matcher import template_matcher
from app.services.auth import get_current_agent
from app.models.agent import Agent

router = APIRouter(prefix="/classify", tags=["classification"])

@router.post("", response_model=ClassificationResponse)
async def classify_ticket(
    request: ClassifyRequest,
    db: Session = Depends(get_db),
    _: Agent = Depends(get_current_agent)
):
    # run ML inference in thread pool — keeps event loop free
    result = await run_in_threadpool(classifier.classify, request.text)
    sentiment = analyze_sentiment(request.text)
    urgency = score_urgency(request.text)
    team = get_assigned_team(result["intent"])
    templates = template_matcher.match(request.text, result["intent"])

    return ClassificationResponse(
        intent=result["intent"],
        confidence=result["confidence"],
        needs_review=result["needs_review"],
        all_scores=result["all_scores"],
        urgency=urgency,
        sentiment=sentiment["label"],
        sentiment_score=sentiment["score"],
        assigned_team=team,
        templates=templates
    )