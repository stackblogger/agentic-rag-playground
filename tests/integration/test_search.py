import litellm

PETS = [(1, "Cats sleep 12 to 16 hours a day."), (2, "Dogs need daily walks.")]


def test_closest_chunk_comes_first(client, add_document):
    add_document("pets.pdf", PETS)

    response = client.get("/search", params={"query": "how long do cats sleep?"})

    assert response.status_code == 200
    first, second = response.json()
    assert first["content"] == PETS[0][1]
    assert (first["filename"], first["page_number"]) == ("pets.pdf", 1)
    assert first["score"] > second["score"]


def test_limit_is_used(client, add_document):
    add_document("pets.pdf", PETS)
    assert len(client.get("/search", params={"query": "cats", "limit": 1}).json()) == 1


def test_chunks_without_embedding_are_skipped(client, add_document):
    add_document("pets.pdf", PETS, embed=False)
    assert client.get("/search", params={"query": "cats"}).json() == []


def test_wrong_input_gives_422(client):
    assert client.get("/search", params={"query": ""}).status_code == 422
    assert client.get("/search", params={"query": "cats", "limit": 99}).status_code == 422


def test_embedding_failure_gives_502(client, monkeypatch):
    def broken(model, input):
        raise RuntimeError("no key")

    monkeypatch.setattr(litellm, "embedding", broken)
    assert client.get("/search", params={"query": "cats"}).status_code == 502
