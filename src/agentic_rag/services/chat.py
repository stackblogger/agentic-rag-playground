from sqlalchemy.orm import Session

from agentic_rag.agents.rag_agent import run_agent


def chat(db: Session, question: str, limit: int) -> dict:
    return run_agent(db, question, limit)
