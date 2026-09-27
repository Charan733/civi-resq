from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.schemas import AssistantQuery, AssistantResponse
from app.services.assistant import answer_question

router = APIRouter(prefix="/api/assistant", tags=["CIVI-AI Assistant"])


@router.post("/ask", response_model=AssistantResponse)
def ask(payload: AssistantQuery, db: Session = Depends(get_db)):
    """
    Answer a natural-language question using real system data (risk scores, SHAP
    explanations, interventions, or a live simulator run) -- never fabricated.
    """
    result = answer_question(db, payload.question, payload.zone_id)
    return result
