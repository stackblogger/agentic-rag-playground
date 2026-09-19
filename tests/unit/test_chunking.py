from agentic_rag.ingestion.chunking import chunk_text

WORDS = [f"word{i}" for i in range(300)]


def test_empty_and_short_text():
    assert chunk_text("  ", 100, 20) == []
    assert chunk_text("  short text ", 100, 20) == ["short text"]


def test_chunks_are_not_longer_than_size():
    chunks = chunk_text(" ".join(WORDS), 100, 20)
    assert len(chunks) > 1
    assert all(len(chunk) <= 100 for chunk in chunks)


def test_words_are_not_cut_and_all_text_is_covered():
    chunks = chunk_text(" ".join(WORDS), 100, 20)
    assert {word for chunk in chunks for word in chunk.split()} == set(WORDS)


def test_text_without_spaces_is_cut_at_size():
    assert len(chunk_text("x" * 250, 100, 20)) == 3
