from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.agent import Agent
from app.schemas.agent import TokenResponse, AgentResponse
from app.services.auth import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    agent = db.query(Agent).filter(Agent.email == form_data.username).first()
    if not agent or not verify_password(form_data.password, agent.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    token = create_access_token({"sub": agent.id, "role": agent.role})
    return TokenResponse(
        access_token=token,
        agent=AgentResponse.model_validate(agent)
    )