from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.connection import get_db
from ai.orchestrator import ask
from schemas.responses import AskResponse, ChatMessage

router = APIRouter(prefix="/api", tags=["ask"])


class AskRequest(BaseModel):
    question: str
    history: list[ChatMessage] = []


@router.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest, db: Session = Depends(get_db)):
    """
    Natural language analytics query endpoint.
    Accepts conversation history for multi-turn clarification.
    """
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question must not be empty.")

    try:
        history = [{"role": m.role, "content": m.content} for m in request.history]
        result = ask(request.question.strip(), history, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result
