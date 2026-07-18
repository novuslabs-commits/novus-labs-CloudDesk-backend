from pydantic import BaseModel,Field
from typing import Optional

class ClassifyRequest(BaseModel):
    text: str = Field(..., min_length=5)

class TemplateSuggestion(BaseModel):
    template_id: int
    title: str
    body: str
    similarity: float

class ClassificationResponse(BaseModel):
    intent: str
    confidence: float
    needs_review: bool
    all_scores: dict[str, float]
    urgency: str
    sentiment: str
    sentiment_score: float
    assigned_team: str
    templates: list[TemplateSuggestion]