import json
import logging

from sqlalchemy.orm import Session

from agentic_rag.core.config import settings
from agentic_rag.llm.chat import chat_completion
from agentic_rag.services.errors import LLMError
from agentic_rag.services.search import search_documents

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You answer questions about the documents that the user uploaded. "
    "Use the search_documents tool to find information. "
    "If the results are not enough, search again with different words. "
    "Answer only from the search results. "
    "If the answer is not there, say that you could not find it in the documents."
)

SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search_documents",
        "description": "Search the uploaded documents and get the chunks that match the query best.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "What to search for"}},
            "required": ["query"],
        },
    },
}


def ask_llm(messages: list[dict], tools: list[dict] | None = None):
    try:
        return chat_completion(messages, tools)
    except Exception:
        logger.exception("The LLM call failed")
        raise LLMError("Could not get an answer from the LLM")


def run_search_tool(db: Session, arguments: str, limit: int, sources: list[dict]) -> str:
    try:
        query = json.loads(arguments)["query"]
    except (ValueError, KeyError, TypeError):
        logger.warning("The LLM gave wrong arguments for the search tool")
        logger.debug("Arguments were: %s", arguments)
        return "Invalid arguments. A query is needed."

    logger.debug("Search query from the LLM: %s", query)
    known = {source["chunk_id"]: source["number"] for source in sources}
    lines = []
    results = search_documents(db, query, limit)
    logger.info("Search tool found %d chunks", len(results))
    for result in results:
        number = known.get(result["chunk_id"])
        if number is None:
            number = len(sources) + 1
            sources.append(
                {
                    "number": number,
                    "chunk_id": result["chunk_id"],
                    "document_id": result["document_id"],
                    "filename": result["filename"],
                    "page_number": result["page_number"],
                }
            )
        lines.append(f"[{number}] {result['filename']} (page {result['page_number']})\n{result['content']}")

    return "\n\n".join(lines) if lines else "No results found."


def run_agent(db: Session, question: str, limit: int) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    sources: list[dict] = []
    logger.info("Agent started: question_length=%d, limit=%d, max_steps=%d", len(question), limit, settings.agent_max_steps)

    for step in range(1, settings.agent_max_steps + 1):
        message = ask_llm(messages, tools=[SEARCH_TOOL])
        if not message.tool_calls:
            logger.info("Agent finished after %d step(s) with %d source(s)", step, len(sources))
            return {"answer": message.content, "sources": sources}
        logger.info("Agent step %d: the LLM wants to search (%d call(s))", step, len(message.tool_calls))

        messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {"name": call.function.name, "arguments": call.function.arguments},
                    }
                    for call in message.tool_calls
                ],
            }
        )
        for call in message.tool_calls:
            if call.function.name == "search_documents":
                content = run_search_tool(db, call.function.arguments, limit, sources)
            else:
                logger.warning("The LLM asked for an unknown tool: %s", call.function.name)
                content = "Unknown tool."
            messages.append({"role": "tool", "tool_call_id": call.id, "content": content})

    # searched enough, ask for the final answer without the tool
    logger.info("Agent reached the limit of %d searches, asking for the final answer", settings.agent_max_steps)
    message = ask_llm(messages)
    return {"answer": message.content, "sources": sources}
