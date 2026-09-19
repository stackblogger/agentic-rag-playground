from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from agentic_rag.db.connection import get_db

app = FastAPI(title="Agentic RAG Playground")


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
