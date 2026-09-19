import litellm

from agentic_rag.core.config import settings


def generate_answer(messages: list[dict]) -> str:
    response = litellm.completion(model=settings.llm_model, messages=messages)
    return response.choices[0].message.content
