import litellm

from agentic_rag.core.config import settings


def chat_completion(messages: list[dict], tools: list[dict] | None = None):
    kwargs = {"model": settings.llm_model, "messages": messages}
    if tools:
        kwargs["tools"] = tools
    response = litellm.completion(**kwargs)
    return response.choices[0].message
