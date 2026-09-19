from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from agentic_rag.db.connection import get_db
from agentic_rag.services import search as search_service
from agentic_rag.services.errors import EmbeddingError

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
def search(
    query: str = Query(min_length=1),
    limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    try:
        return search_service.search_documents(db, query, limit)
    except EmbeddingError as error:
        raise HTTPException(status_code=502, detail=str(error))
