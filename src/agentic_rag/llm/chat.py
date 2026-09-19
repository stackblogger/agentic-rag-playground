import logging

import litellm

from agentic_rag.core.config import settings

logger = logging.getLogger(__name__)


def chat_completion(messages: list[dict], tools: list[dict] | None = None):
    kwargs = {"model": settings.llm_model, "messages": messages}
    if tools:
        kwargs["tools"] = tools
    logger.debug("Calling the LLM %s with %d messages (tools: %s)", settings.llm_model, len(messages), bool(tools))
    response = litellm.completion(**kwargs)
    return response.choices[0].message
