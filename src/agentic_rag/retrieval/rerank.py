import json
import logging

from agentic_rag.llm.chat import chat_completion

logger = logging.getLogger(__name__)

PROMPT = (
    "Rank these search results by how well they answer the query. "
    "Reply with only a JSON array of the result numbers, best match first. "
    "Example: [3, 1, 2]\n\n"
    "Query: {query}\n\n"
    "{listing}"
)


def rerank_chunks(query: str, chunks: list[dict], limit: int) -> list[dict]:
    """Puts the most relevant chunks first, using the chat LLM. Keeps the given order if that fails."""
    if len(chunks) <= 1:
        return chunks[:limit]

    listing = "\n\n".join(f"{index + 1}. {chunk['content']}" for index, chunk in enumerate(chunks))
    messages = [{"role": "user", "content": PROMPT.format(query=query, listing=listing)}]

    try:
        message = chat_completion(messages)
        order = json.loads(message.content)
    except Exception:
        logger.exception("Reranking failed, keeping the vector search order")
        return chunks[:limit]

    ranked = []
    used = set()
    for number in order:
        index = number - 1 if isinstance(number, int) else -1
        if 0 <= index < len(chunks) and index not in used:
            ranked.append(chunks[index])
            used.add(index)
        if len(ranked) == limit:
            break

    for index, chunk in enumerate(chunks):
        if len(ranked) == limit:
            break
        if index not in used:
            ranked.append(chunk)
            used.add(index)

    return ranked
