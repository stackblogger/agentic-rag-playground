import json
from types import SimpleNamespace

import litellm

PETS = [(1, "Cats sleep 12 to 16 hours a day."), (2, "Dogs need daily walks.")]


def answer(text):
    return SimpleNamespace(content=text, tool_calls=None)


def search(query):
    function = SimpleNamespace(name="search_documents", arguments=json.dumps({"query": query}))
    return SimpleNamespace(content=None, tool_calls=[SimpleNamespace(id="call1", function=function)])


def test_chat_searches_the_documents_and_answers(client, add_document, fake_llm):
    add_document("pets.pdf", PETS)
    calls = fake_llm([search("cats sleep"), answer("Cats sleep 12 to 16 hours.")])

    response = client.post("/chat", json={"question": "How long do cats sleep?", "limit": 1})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Cats sleep 12 to 16 hours."
    assert body["sources"][0]["filename"] == "pets.pdf"
    assert body["sources"][0]["page_number"] == 1
    # the chunk found in the database was given to the LLM
    tool_message = calls[1][-1]
    assert tool_message["role"] == "tool"
    assert PETS[0][1] in tool_message["content"]


def test_chat_can_answer_without_searching(client, fake_llm):
    fake_llm([answer("Hello!")])
    response = client.post("/chat", json={"question": "hi"})
    assert response.json() == {"answer": "Hello!", "sources": []}


def test_wrong_input_gives_422(client):
    assert client.post("/chat", json={"question": ""}).status_code == 422
    assert client.post("/chat", json={"question": "hi", "limit": 50}).status_code == 422


def test_llm_failure_gives_502(client, monkeypatch):
    def broken(model, messages, tools=None):
        raise RuntimeError("provider down")

    monkeypatch.setattr(litellm, "completion", broken)
    assert client.post("/chat", json={"question": "hi"}).status_code == 502


def test_embedding_failure_during_search_gives_502(client, fake_llm, monkeypatch):
    fake_llm([search("cats")])

    def broken(model, input):
        raise RuntimeError("no key")

    monkeypatch.setattr(litellm, "embedding", broken)
    assert client.post("/chat", json={"question": "cats?"}).status_code == 502
