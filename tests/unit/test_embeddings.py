from types import SimpleNamespace

import litellm

from agentic_rag.llm.embeddings import BATCH_SIZE, embed_texts


def fake_embedding(calls):
    def fake(model, input):
        calls.append(list(input))
        return SimpleNamespace(data=[{"embedding": [float(len(text))]} for text in input])

    return fake


def test_empty_list_does_not_call_the_provider(monkeypatch):
    calls = []
    monkeypatch.setattr(litellm, "embedding", fake_embedding(calls))
    assert embed_texts([]) == []
    assert calls == []


def test_texts_are_sent_in_batches_and_order_is_kept(monkeypatch):
    calls = []
    monkeypatch.setattr(litellm, "embedding", fake_embedding(calls))
    texts = ["a" * (i + 1) for i in range(250)]

    vectors = embed_texts(texts)

    assert [len(batch) for batch in calls] == [BATCH_SIZE, BATCH_SIZE, 50]
    assert vectors == [[float(i + 1)] for i in range(250)]
