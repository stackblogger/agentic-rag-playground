from sqlalchemy.orm import Session

from agentic_rag.llm.chat import generate_answer
from agentic_rag.services.errors import LLMError
from agentic_rag.services.search import search_documents

SYSTEM_PROMPT = (
    "You answer questions using only the context given by the user. "
    "If the answer is not in the context, say that you could not find it in the documents. "
)

NOT_FOUND_ANSWER = "I could not find anything in the documents."


def build_context(results: list[dict]) -> str:
    parts = []
    for number, result in enumerate(results, start=1):
        parts.append(f"[{number}] {result['filename']} (page {result['page_number']})\n{result['content']}")
    return "\n\n".join(parts)


def chat(db: Session, question: str, limit: int) -> dict:
    results = search_documents(db, question, limit)
    if not results:
        return {"answer": NOT_FOUND_ANSWER, "sources": []}

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context:\n{build_context(results)}\n\nQuestion: {question}"},
    ]
    try:
        answer = generate_answer(messages)
    except Exception:
        raise LLMError("Could not get an answer from the LLM")

    sources = [
        {
            "number": number,
            "chunk_id": result["chunk_id"],
            "document_id": result["document_id"],
            "filename": result["filename"],
            "page_number": result["page_number"],
        }
        for number, result in enumerate(results, start=1)
    ]
    return {"answer": answer, "sources": sources}
