import logging
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from agentic_rag.api.chat import router as chat_router
from agentic_rag.api.documents import router as documents_router
from agentic_rag.api.search import router as search_router
from agentic_rag.core.logging import setup_logging
from agentic_rag.db.connection import get_db

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Agentic RAG Playground")
app.include_router(documents_router)
app.include_router(search_router)
app.include_router(chat_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Database health check failed")
        raise HTTPException(status_code=503, detail="Database is not reachable")
    return {"status": "ok"}


# keep this last, so the API routes above are matched first
app.mount("/", StaticFiles(directory=Path(__file__).resolve().parent.parent / "ui", html=True), name="ui")
