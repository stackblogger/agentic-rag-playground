import litellm

from agentic_rag.core.config import settings

BATCH_SIZE = 100


def embed_texts(texts: list[str]) -> list[list[float]]:
    vectors = []
    for start in range(0, len(texts), BATCH_SIZE):
        batch = texts[start : start + BATCH_SIZE]
        response = litellm.embedding(model=settings.embedding_model, input=batch)
        vectors.extend(item["embedding"] for item in response.data)
    return vectors
