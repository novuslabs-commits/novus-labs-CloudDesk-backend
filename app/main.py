from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base, SessionLocal
from app.config import get_settings
from app.services.classifier import classifier
from app.services.template_matcher import template_matcher
from app.routers import auth, agents, tickets, classification, feedback,metrics,templates
import app.models

settings = get_settings()
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Support Intelligence API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.on_event("startup")
def startup():
    db = SessionLocal()
    try:
        template_matcher.fit(db)
    finally:
        db.close()

app.include_router(auth.router)
app.include_router(agents.router)
app.include_router(tickets.router)
app.include_router(classification.router)
app.include_router(feedback.router)
app.include_router(metrics.router)
app.include_router(templates.router)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "classifier_device": str(classifier.device),
        "templates_fitted": template_matcher.fitted
    }