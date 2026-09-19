from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from agentic_rag.db.connection import get_db
from agentic_rag.services import chat as chat_service
from agentic_rag.services.errors import EmbeddingError, LLMError

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=10)


@router.post("")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        return chat_service.chat(db, request.question, request.limit)
    except (EmbeddingError, LLMError) as error:
        raise HTTPException(status_code=502, detail=str(error))
