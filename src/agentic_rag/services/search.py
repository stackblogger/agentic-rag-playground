from sqlalchemy.orm import Session

from agentic_rag.llm.embeddings import embed_texts
from agentic_rag.retrieval.search import find_similar_chunks
from agentic_rag.services.errors import EmbeddingError


def search_documents(db: Session, query: str, limit: int) -> list[dict]:
    try:
        query_vector = embed_texts([query])[0]
    except Exception:
        raise EmbeddingError("Could not create embeddings")

    rows = find_similar_chunks(db, query_vector, limit)
    return [
        {
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "filename": filename,
            "page_number": chunk.page_number,
            "content": chunk.content,
            "score": round(1 - distance, 4),
        }
        for chunk, filename, distance in rows
    ]
