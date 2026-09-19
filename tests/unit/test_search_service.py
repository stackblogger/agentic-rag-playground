from types import SimpleNamespace

import pytest

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
