from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from agentic_rag.api.documents import router as documents_router
from agentic_rag.api.search import router as search_router
from agentic_rag.db.connection import get_db

app = FastAPI(title="Agentic RAG Playground")
app.include_router(documents_router)
app.include_router(search_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="Database is not reachable")
    return {"status": "ok"}
