from types import SimpleNamespace

import pytest

from agentic_rag.core.config import settings
from agentic_rag.services import search
from agentic_rag.services.errors import EmbeddingError


def test_result_has_the_expected_fields_and_score(monkeypatch):
    chunk = SimpleNamespace(id=1, document_id=7, page_number=3, content="cats sleep a lot")
    monkeypatch.setattr(search, "embed_texts", lambda texts: [[0.1]])
    monkeypatch.setattr(search, "find_similar_chunks", lambda db, vector, limit: [(chunk, "cats.pdf", 0.123456)])

    assert search.search_documents(None, "cats", 5) == [
        {
            "chunk_id": 1,
            "document_id": 7,
            "filename": "cats.pdf",
            "page_number": 3,
            "content": "cats sleep a lot",
            "score": 0.8765,
        }
    ]


def test_embedding_failure_raises_embedding_error(monkeypatch):
    def broken(texts):
        raise RuntimeError("no key")

    monkeypatch.setattr(search, "embed_texts", broken)
    with pytest.raises(EmbeddingError):
        search.search_documents(None, "cats", 5)


def test_rerank_is_applied_when_enabled(monkeypatch):
    first = SimpleNamespace(id=1, document_id=7, page_number=1, content="first")
    second = SimpleNamespace(id=2, document_id=7, page_number=1, content="second")
    monkeypatch.setattr(search, "embed_texts", lambda texts: [[0.1]])
    monkeypatch.setattr(
        search, "find_similar_chunks", lambda db, vector, limit: [(first, "a.pdf", 0.1), (second, "a.pdf", 0.2)]
    )
    monkeypatch.setattr(search, "rerank_chunks", lambda query, results, limit: list(reversed(results))[:limit])
    monkeypatch.setattr(settings, "rerank_enabled", True)

    result = search.search_documents(None, "q", 2)

    assert [item["chunk_id"] for item in result] == [2, 1]


def test_rerank_is_skipped_when_disabled(monkeypatch):
    def broken(query, results, limit):
        raise AssertionError("rerank should not be called when disabled")

    chunk = SimpleNamespace(id=1, document_id=7, page_number=1, content="first")
    monkeypatch.setattr(search, "embed_texts", lambda texts: [[0.1]])
    monkeypatch.setattr(search, "find_similar_chunks", lambda db, vector, limit: [(chunk, "a.pdf", 0.1)])
    monkeypatch.setattr(search, "rerank_chunks", broken)
    monkeypatch.setattr(settings, "rerank_enabled", False)

    result = search.search_documents(None, "q", 5)

    assert [item["chunk_id"] for item in result] == [1]
