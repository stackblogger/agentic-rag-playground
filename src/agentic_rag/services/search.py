import logging

from sqlalchemy.orm import Session

from agentic_rag.core.config import settings
from agentic_rag.llm.embeddings import embed_texts
from agentic_rag.retrieval.rerank import rerank_chunks
from agentic_rag.retrieval.search import find_similar_chunks
from agentic_rag.services.errors import EmbeddingError

logger = logging.getLogger(__name__)

# when reranking, more candidates are fetched than asked for, so the LLM has more to choose from
CANDIDATE_MULTIPLIER = 4
MAX_CANDIDATES = 30


def search_documents(db: Session, query: str, limit: int) -> list[dict]:
    try:
        query_vector = embed_texts([query])[0]
    except Exception:
        logger.exception("Could not create the embedding of the search query")
        raise EmbeddingError("Could not create embeddings")

    fetch_limit = min(limit * CANDIDATE_MULTIPLIER, MAX_CANDIDATES) if settings.rerank_enabled else limit
    rows = find_similar_chunks(db, query_vector, fetch_limit)
    logger.info("Search done: query_length=%d, limit=%d, results=%d", len(query), limit, len(rows))
    logger.debug("Search query: %s", query)

    results = [
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

    if settings.rerank_enabled and results:
        return rerank_chunks(query, results, limit)
    return results[:limit]
