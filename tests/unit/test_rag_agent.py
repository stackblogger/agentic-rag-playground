import json
from types import SimpleNamespace

import pytest

from agentic_rag.agents import rag_agent
from agentic_rag.core.config import settings
from agentic_rag.services.errors import LLMError


def answer(text):
    return SimpleNamespace(content=text, tool_calls=None)


def search(call_id, query):
    function = SimpleNamespace(name="search_documents", arguments=json.dumps({"query": query}))
    return SimpleNamespace(content=None, tool_calls=[SimpleNamespace(id=call_id, function=function)])


def found(chunk_id, filename="cats.pdf"):
    return {"chunk_id": chunk_id, "document_id": 1, "filename": filename, "page_number": 1, "content": "text"}


def use_fakes(monkeypatch, replies, results):
    """The LLM gives the replies one by one. The search gives the results for each query."""
    tools_used = []

    def fake_llm(messages, tools=None):
        tools_used.append(tools is not None)
        return replies.pop(0)

    monkeypatch.setattr(rag_agent, "chat_completion", fake_llm)
    monkeypatch.setattr(rag_agent, "search_documents", lambda db, query, limit: results.get(query, []))
    monkeypatch.setattr(settings, "agent_max_steps", 3)
    return tools_used


def test_answer_without_search(monkeypatch):
    use_fakes(monkeypatch, [answer("Hello!")], {})
    assert rag_agent.run_agent(None, "hi", 5) == {"answer": "Hello!", "sources": []}


def test_search_then_answer_gives_sources(monkeypatch):
    use_fakes(monkeypatch, [search("a", "cats"), answer("12 to 16 hours")], {"cats": [found(10)]})

    response = rag_agent.run_agent(None, "cats?", 5)

    assert response["answer"] == "12 to 16 hours"
    assert response["sources"] == [
        {"number": 1, "chunk_id": 10, "document_id": 1, "filename": "cats.pdf", "page_number": 1}
    ]


def test_same_chunk_found_twice_keeps_one_number(monkeypatch):
    results = {"cats": [found(10)], "dogs": [found(20, "dogs.pdf")], "cats again": [found(10)]}
    use_fakes(monkeypatch, [search("a", "cats"), search("b", "dogs"), search("c", "cats again"), answer("done")], results)

    sources = rag_agent.run_agent(None, "compare", 5)["sources"]

    assert [(source["number"], source["chunk_id"]) for source in sources] == [(1, 10), (2, 20)]


def test_after_max_steps_the_llm_must_answer_without_the_tool(monkeypatch):
    replies = [search(str(i), "cats") for i in range(3)] + [answer("best answer so far")]
    tools_used = use_fakes(monkeypatch, replies, {"cats": [found(10)]})

    assert rag_agent.run_agent(None, "x", 5)["answer"] == "best answer so far"
    assert tools_used == [True, True, True, False]


def test_llm_failure_raises_llm_error(monkeypatch):
    def broken(messages, tools=None):
        raise RuntimeError("provider down")

    monkeypatch.setattr(rag_agent, "chat_completion", broken)
    with pytest.raises(LLMError):
        rag_agent.run_agent(None, "x", 5)
