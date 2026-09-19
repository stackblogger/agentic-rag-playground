# Agentic RAG Playground

A simple playground for developers to try Agentic RAG. Documents can be uploaded, and then devs can chat with them or search inside them.

## What is this?

RAG means "Retrieval Augmented Generation". In simple words: we first find the useful parts from the documents, then we give those parts to the LLM so it can answer properly.

"Agentic" means the LLM is not just answering once. It can decide by itself what to do, like searching again with a better query if the first result is not good.

This repo is for learning and experimenting. Devs can clone it, play with it, break it, and improve it.

## Tech stack

- Python 3.11+
- PostgreSQL with pgvector (to store text chunks and embeddings)
- LiteLLM (one interface for many LLM providers)
- pypdf (to extract text from PDF files)
- FastAPI (for the API)
- Tabler (Bootstrap based UI template, loaded from a CDN) with plain JavaScript, no build step
- SQLAlchemy (ORM) and Alembic (database migrations)
- Docker Compose (to run Postgres locally)

## Folder structure

```
agentic-rag-playground/
├── src/agentic_rag/
│   ├── api/          # API routes, only take the request and give the response (upload, search, chat)
│   ├── core/         # config, settings, logging
│   ├── services/     # main logic of each feature, used by the API routes
│   ├── db/           # database connection and models (SQLAlchemy)
│   ├── ingestion/    # read file, extract text, make chunks
│   ├── retrieval/    # database queries for search
│   ├── agents/       # chat agent, decides what to search and when
│   ├── llm/          # LiteLLM wrapper
│   └── ui/           # web UI (plain HTML, CSS and JS, served by the app)
├── migrations/       # Alembic migration files
├── alembic.ini       # Alembic config
├── tests/
│   ├── unit/         # small tests
│   └── integration/  # tests that need DB / API
├── scripts/          # helper scripts
├── docs/             # extra notes and design docs
├── data/uploads/     # uploaded files are kept here
└── docker/           # Docker related files
```

## How to run

1. Clone the repo

   ```bash
   git clone https://github.com/stackblogger/agentic-rag-playground.git
   cd agentic-rag-playground
   ```

2. Make a virtual environment and install packages

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Copy the env file. The defaults work for local run, change the values if needed. Set `OPENAI_API_KEY` in it, because embeddings are made with OpenAI.

   ```bash
   cp .env.example .env
   ```

4. Start Postgres (with pgvector) in Docker. The container name is `agentic-rag-db`.

   ```bash
   docker compose up -d
   ```

   The db user, password and name are `postgres`, `postgres` and `agentic_rag`, same as the default `DATABASE_URL`. Data is kept in a Docker volume, so it stays even if the container is restarted.

5. Run the database migrations. This turns on the pgvector extension and creates the tables.

   ```bash
   alembic upgrade head
   ```

6. Start the app

   ```bash
   uvicorn agentic_rag.api.main:app --app-dir src --reload
   ```

7. Open http://127.0.0.1:8000 for the web UI. The Status page shows if the API and the database are working. API docs are at http://127.0.0.1:8000/docs, and http://127.0.0.1:8000/health returns `{"status": "ok"}`.

8. Check the database connection. Open http://127.0.0.1:8000/health/db. It shows `{"status": "ok"}` when Postgres is reachable, and a 503 error when it is not.

## How to use

### Upload a PDF

```bash
curl -X POST http://127.0.0.1:8000/documents -F "file=@/path/to/file.pdf"
```

The file is saved in `UPLOAD_DIR` and the text is extracted page by page with pypdf. The text is saved in the database, and then cut into small chunks. An embedding is made for each chunk with LiteLLM (OpenAI by default) and saved with the chunk, so it can be searched. The response looks like this:

```json
{"id": 1, "filename": "file.pdf", "page_count": 12, "chunk_count": 34, "status": "processed"}
```

- Chunks are cut page by page, so a chunk never goes across two pages. Each chunk keeps its page number. Chunks next to each other share some text (`CHUNK_OVERLAP`), so a sentence at the edge is not lost. Words are not cut in the middle when possible.
- Only `.pdf` files are allowed. Other files get a 400 error.
- If pypdf cannot read the file, the response is a 422 error and the document is saved with status `failed`.
- If the embeddings cannot be made (for example the API key is missing or wrong), the response is a 502 error, the document is saved with status `failed`, and no chunks are saved.
- PDFs that are only scanned images have no text to extract, so the saved text will be empty.

The upload can also be tried from the API docs page at http://127.0.0.1:8000/docs.

### List documents

```bash
curl http://127.0.0.1:8000/documents
```

This gives all uploaded documents, newest first, with their page count, chunk count, size and status.

### Delete a document

```bash
curl -X DELETE http://127.0.0.1:8000/documents/1
```

This removes the document, all its chunks and the saved file. The response is 204 when it is done, and 404 if the id does not exist.

### Search

```bash
curl "http://127.0.0.1:8000/search?query=how%20long%20do%20cats%20sleep&limit=5"
```

The query is converted to an embedding with the same model, and the chunks with the closest meaning are returned, best match first. `limit` is how many chunks to return. It is 5 by default and can be from 1 to 20. Each result looks like this:

```json
{
  "chunk_id": 26,
  "document_id": 16,
  "filename": "file.pdf",
  "page_number": 1,
  "content": "text of the chunk...",
  "score": 0.83
}
```

- `score` is cosine similarity. Higher is better, and 1 means the same meaning.
- Chunks without an embedding are skipped.
- An empty query gives a 422 error. If the embedding cannot be made, the response is a 502 error.

### Chat

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "How long do cats sleep in a day?", "limit": 5}'
```

The LLM (`LLM_MODEL`) works as an agent here. It has a search tool for the documents and decides by itself what to search. If the first results are not enough, it searches again with different words, and then it answers only from what it found. `limit` is how many chunks each search gives back. It is 5 by default and can be from 1 to 10. The response looks like this:

```json
{
  "answer": "Cats sleep about 12 to 16 hours in a day.",
  "sources": [
    {"number": 1, "chunk_id": 26, "document_id": 16, "filename": "file.pdf", "page_number": 1}
  ]
}
```

- `sources` lists the chunks the agent found while searching, numbered in the order it found them.
- The agent searches at most `AGENT_MAX_STEPS` times. After that it has to answer with what it has.
- If nothing is found in the documents, the answer says so and `sources` is empty.
- The model in `LLM_MODEL` must support tool calling. OpenAI chat models do.
- An empty question gives a 422 error. If the embedding or the LLM call fails, the response is a 502 error.

## Database migrations

Tables are managed with Alembic. Migration files are in `migrations/versions/`. The database URL is taken from `DATABASE_URL` in the settings, not from `alembic.ini`.

After changing a model in `src/agentic_rag/db/models.py`, make a new migration and apply it:

```bash
alembic revision --autogenerate -m "short message"
alembic upgrade head
```

Always read the generated file before applying it. To undo the last migration, run `alembic downgrade -1`.

Embeddings are stored with 1536 dimensions, which matches the default `EMBEDDING_MODEL` (`text-embedding-3-small`). If a model with a different size is used, change `EMBEDDING_DIMENSIONS` in `src/agentic_rag/db/models.py` and make a new migration.

## Settings

All settings are read from environment variables or the `.env` file (see `.env.example`).

| Name | What it is | Default |
| --- | --- | --- |
| `DATABASE_URL` | Postgres connection string | `postgresql+psycopg://postgres:postgres@localhost:5432/agentic_rag` |
| `UPLOAD_DIR` | Folder where uploaded files are kept | `data/uploads` |
| `LLM_MODEL` | Model name used for chat (any LiteLLM model) | `gpt-4o-mini` |
| `EMBEDDING_MODEL` | Model name used for embeddings | `text-embedding-3-small` |
| `OPENAI_API_KEY` | API key for OpenAI, read by LiteLLM | empty |
| `CHUNK_SIZE` | Maximum number of characters in one chunk | `1000` |
| `CHUNK_OVERLAP` | Number of characters shared between two chunks next to each other | `200` |
| `AGENT_MAX_STEPS` | Maximum number of times the chat agent can search before it must answer | `3` |

The app runs on the local machine and Postgres runs inside Docker, so the host in `DATABASE_URL` must be `localhost`. The container name `agentic-rag-db` only works from another container in the same Docker network.

## Contributing

Please keep changes small, one thing at a time, so commit history stays easy to read. Open an issue first if the change is big.
