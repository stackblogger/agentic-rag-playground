def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    text = text.strip()
    chunks = []
    start = 0

    while start < len(text):
        end = min(start + size, len(text))

        # try not to cut a word in the middle
        if end < len(text):
            last_space = text.rfind(" ", start, end)
            if last_space > start + size // 2:
                end = last_space

        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)

        if end >= len(text):
            break
        start = max(end - overlap, start + 1)

    return chunks
