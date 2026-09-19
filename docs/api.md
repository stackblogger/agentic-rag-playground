# API

Base URL is `http://127.0.0.1:8000`. Live docs with a "Try it out" button are at `/docs`.

| Method | Route | What it does |
| --- | --- | --- |
| GET | `/health` | Checks the API |
| GET | `/health/db` | Checks the database |
| POST | `/documents` | Uploads a PDF |
| GET | `/documents` | Lists documents |
| DELETE | `/documents/{id}` | Deletes a document |
| GET | `/search` | Searches the chunks |
| POST | `/chat` | Asks a question |

## Health

```bash
curl http://127.0.0.1:8000/health
```

Returns `{"status": "ok"}`. `/health/db` returns the same, or a 503 error if Postgres is not reachable.

## Upload a document

```bash
curl -X POST http://127.0.0.1:8000/documents -F "file=@/path/to/file.pdf"
```

```json
{"id": 1, "filename": "file.pdf", "page_count": 12, "chunk_count": 34, "status": "processed"}
```

Errors: 400 if the file is not a PDF, 422 if the PDF cannot be read, 502 if the embeddings cannot be made.

## List documents

```bash
curl http://127.0.0.1:8000/documents
```

Returns a list, newest first. Each item has `id`, `filename`, `page_count`, `chunk_count`, `size_bytes`, `status` and `created_at`.

## Delete a document

```bash
curl -X DELETE http://127.0.0.1:8000/documents/1
```

Returns 204 when done, and 404 if the id does not exist. The chunks and the saved file are deleted too.

## Search

```bash
curl "http://127.0.0.1:8000/search?query=how%20long%20do%20cats%20sleep&limit=5"
```

`limit` is from 1 to 20 (default 5).

```json
[
  {
    "chunk_id": 26,
    "document_id": 16,
    "filename": "file.pdf",
    "page_number": 1,
    "content": "text of the chunk...",
    "score": 0.83
  }
]
```

Errors: 422 for an empty query or a wrong `limit`, 502 if the embedding cannot be made.

## Chat

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "How long do cats sleep in a day?", "limit": 5}'
```

`limit` is how many chunks each search gives back, from 1 to 10 (default 5).

```json
{
  "answer": "Cats sleep about 12 to 16 hours in a day.",
  "sources": [
    {"number": 1, "chunk_id": 26, "document_id": 16, "filename": "file.pdf", "page_number": 1}
  ]
}
```

Errors: 422 for an empty question, 502 if the embedding or the LLM call fails.
