from types import SimpleNamespace

from agentic_rag.retrieval import rerank


def chunk(number):
    return {"chunk_id": number, "content": f"chunk {number}"}


def test_single_chunk_is_returned_without_calling_the_llm(monkeypatch):
    def broken(messages):
        raise AssertionError("should not call the LLM for a single chunk")

    monkeypatch.setattr(rerank, "chat_completion", broken)
    assert rerank.rerank_chunks("q", [chunk(1)], 5) == [chunk(1)]


def test_chunks_are_reordered_by_the_llm(monkeypatch):
    monkeypatch.setattr(rerank, "chat_completion", lambda messages: SimpleNamespace(content="[2, 1]"))
    result = rerank.rerank_chunks("q", [chunk(1), chunk(2)], 2)
    assert [item["chunk_id"] for item in result] == [2, 1]


def test_result_is_cut_to_the_limit(monkeypatch):
    monkeypatch.setattr(rerank, "chat_completion", lambda messages: SimpleNamespace(content="[3, 2, 1]"))
    result = rerank.rerank_chunks("q", [chunk(1), chunk(2), chunk(3)], 2)
    assert [item["chunk_id"] for item in result] == [3, 2]


def test_missing_numbers_are_filled_with_the_rest_in_order(monkeypatch):
    monkeypatch.setattr(rerank, "chat_completion", lambda messages: SimpleNamespace(content="[2]"))
    result = rerank.rerank_chunks("q", [chunk(1), chunk(2), chunk(3)], 3)
    assert [item["chunk_id"] for item in result] == [2, 1, 3]


def test_llm_failure_keeps_the_vector_search_order(monkeypatch):
    def broken(messages):
        raise RuntimeError("provider down")

    monkeypatch.setattr(rerank, "chat_completion", broken)
    result = rerank.rerank_chunks("q", [chunk(1), chunk(2)], 2)
    assert [item["chunk_id"] for item in result] == [1, 2]


def test_bad_json_keeps_the_vector_search_order(monkeypatch):
    monkeypatch.setattr(rerank, "chat_completion", lambda messages: SimpleNamespace(content="not json"))
    result = rerank.rerank_chunks("q", [chunk(1), chunk(2)], 2)
    assert [item["chunk_id"] for item in result] == [1, 2]
