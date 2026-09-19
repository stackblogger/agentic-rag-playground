from sqlalchemy import select
from sqlalchemy.orm import Session

from agentic_rag.db.models import Chunk, Document


def find_similar_chunks(db: Session, query_vector: list[float], limit: int):
    distance = Chunk.embedding.cosine_distance(query_vector)
    query = (
        select(Chunk, Document.filename, distance.label("distance"))
        .join(Document, Chunk.document_id == Document.id)
        .where(Chunk.embedding.is_not(None))
        .order_by(distance)
        .limit(limit)
    )
    return db.execute(query).all()
