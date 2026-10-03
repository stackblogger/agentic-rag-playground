import asyncio
from types import SimpleNamespace

import litellm
import pytest
from mcp.server.mcpserver.exceptions import ToolError
from sqlalchemy.orm import sessionmaker

from agentic_rag.db.models import Document
from agentic_rag.mcp_server.server import create_server

PETS = [(1, "Cats sleep 12 to 16 hours a day."), (2, "Dogs need daily walks.")]


@pytest.fixture
def server(test_engine):
    return create_server(sessionmaker(bind=test_engine))


def call(server, name, arguments):
    """Calls a tool like an MCP client would and gives back the data the tool returned."""
    return asyncio.run(server.call_tool(name, arguments)).structured_content["result"]


def test_server_has_name_and_tools(server):
    tools = asyncio.run(server.list_tools())
    assert server.name == "agentic-rag"
    assert {tool.name for tool in tools} == {"list_documents", "search_documents"}


def test_list_documents_returns_newest_first(server, add_document):
    add_document("a.pdf", PETS)
    add_document("b.pdf", PETS)

    documents = call(server, "list_documents", {})

    assert [document["filename"] for document in documents] == ["b.pdf", "a.pdf"]
    assert documents[0]["chunk_count"] == 2
    assert set(documents[0]) == {
        "id",
        "filename",
        "page_count",
        "chunk_count",
        "size_bytes",
        "status",
        "created_at",
    }


def test_list_documents_empty(server):
    assert call(server, "list_documents", {}) == []


def test_list_documents_shows_failed_documents(server, db):
    db.add(Document(filename="bad.pdf", file_path="x", status="failed"))
    db.commit()

    documents = call(server, "list_documents", {})

    assert [(document["filename"], document["status"]) for document in documents] == [("bad.pdf", "failed")]


def test_search_returns_closest_chunk_first(server, add_document):
    add_document("pets.pdf", PETS)

    first, second = call(server, "search_documents", {"query": "how long do cats sleep?"})

    assert first["content"] == PETS[0][1]
    assert (first["filename"], first["page_number"]) == ("pets.pdf", 1)
    assert first["score"] > second["score"]


def test_search_limit_is_used(server, add_document):
    add_document("pets.pdf", PETS)
    assert len(call(server, "search_documents", {"query": "cats", "limit": 1})) == 1


def test_search_with_no_documents_gives_empty_list(server):
    assert call(server, "search_documents", {"query": "cats"}) == []


def test_search_can_be_reranked(server, add_document, fake_llm):
    add_document("pets.pdf", PETS)
    fake_llm([SimpleNamespace(content="[2, 1]")])

    first, second = call(server, "search_documents", {"query": "how long do cats sleep?"})

    assert (first["content"], second["content"]) == (PETS[1][1], PETS[0][1])


@pytest.mark.parametrize("arguments", [{"query": ""}, {"query": "cats", "limit": 0}, {"query": "cats", "limit": 99}])
def test_search_rejects_wrong_input(server, arguments):
    with pytest.raises(ToolError):
        call(server, "search_documents", arguments)


def test_search_embedding_failure_gives_clear_error(server, monkeypatch):
    def broken(model, input):
        raise RuntimeError("no key")

    monkeypatch.setattr(litellm, "embedding", broken)

    with pytest.raises(ToolError, match="Could not create embeddings"):
        call(server, "search_documents", {"query": "cats"})


def test_session_is_closed_after_an_error(test_engine, monkeypatch):
    factory = sessionmaker(bind=test_engine)
    closed = []

    def tracked_factory():
        session = factory()
        original_close = session.close
        session.close = lambda: (closed.append(True), original_close())
        return session

    def broken(model, input):
        raise RuntimeError("no key")

    monkeypatch.setattr(litellm, "embedding", broken)

    with pytest.raises(ToolError):
        call(create_server(tracked_factory), "search_documents", {"query": "cats"})

    assert closed == [True]
