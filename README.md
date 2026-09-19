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
- SQLAlchemy (ORM) and Alembic (database migrations)
- Docker Compose (to run Postgres locally)

## Folder structure

```
agentic-rag-playground/
├── src/agentic_rag/
│   ├── api/          # API routes (upload, search, chat)
│   ├── core/         # config, settings, logging
│   ├── db/           # database connection and models (SQLAlchemy)
│   ├── ingestion/    # read file, extract text, make chunks
│   ├── retrieval/    # embeddings and search logic
│   ├── agents/       # agent logic, decides what to search and when
│   └── llm/          # LiteLLM wrapper
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

3. Copy the env file. The defaults work for local run, change the values if needed.

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

7. Check that it is running. Open http://127.0.0.1:8000/health and it should show `{"status": "ok"}`. API docs are at http://127.0.0.1:8000/docs.

8. Check the database connection. Open http://127.0.0.1:8000/health/db. It shows `{"status": "ok"}` when Postgres is reachable, and a 503 error when it is not.

## How to use

### Upload a PDF

```bash
curl -X POST http://127.0.0.1:8000/documents -F "file=@/path/to/file.pdf"
```

The file is saved in `UPLOAD_DIR` and the text is extracted page by page with pypdf. The text is saved in the database, and then cut into small chunks for search. The response looks like this:

```json
{"id": 1, "filename": "file.pdf", "page_count": 12, "chunk_count": 34, "status": "processed"}
```

- Chunks are cut page by page, so a chunk never goes across two pages. Each chunk keeps its page number. Chunks next to each other share some text (`CHUNK_OVERLAP`), so a sentence at the edge is not lost. Words are not cut in the middle when possible.
- Only `.pdf` files are allowed. Other files get a 400 error.
- If pypdf cannot read the file, the response is a 422 error and the document is saved with status `failed`.
- PDFs that are only scanned images have no text to extract, so the saved text will be empty.

The upload can also be tried from the API docs page at http://127.0.0.1:8000/docs.

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
| `CHUNK_SIZE` | Maximum number of characters in one chunk | `1000` |
| `CHUNK_OVERLAP` | Number of characters shared between two chunks next to each other | `200` |

The app runs on the local machine and Postgres runs inside Docker, so the host in `DATABASE_URL` must be `localhost`. The container name `agentic-rag-db` only works from another container in the same Docker network.

## Contributing

Please keep changes small, one thing at a time, so commit history stays easy to read. Open an issue first if the change is big.
