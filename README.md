# Agentic RAG Playground

A simple playground for developers to try Agentic RAG. Upload documents, then chat with them or search inside them.

## What is this?

RAG means "Retrieval Augmented Generation". We first find the useful parts of the documents, then give those parts to the LLM so it can answer properly.

"Agentic" means the LLM decides by itself what to do. For example, it can search again with better words if the first results are not good.

## Architecture

![Architecture of Agentic RAG Playground](docs/agentic-rag-architecture.png)

## Tech stack

- Python 3.11+, FastAPI
- PostgreSQL with pgvector, SQLAlchemy, Alembic
- LiteLLM (one interface for many LLM providers), pypdf
- Web UI with Tabler and plain JavaScript (loaded from a CDN, no build step)
- Docker and Docker Compose

## How to run

### With Docker

```bash
git clone https://github.com/stackblogger/agentic-rag-playground.git
cd agentic-rag-playground
cp .env.example .env        # set OPENAI_API_KEY in it
docker compose up -d --build
```

Open http://127.0.0.1:8000. The app runs the database migrations by itself when it starts.

- Uploaded files are kept in `data/uploads/`. Database data is kept in a Docker volume.
- `DATABASE_URL` and `UPLOAD_DIR` in `.env` are ignored in Docker, because `docker-compose.yml` sets them.
- Logs: `docker compose logs -f app`. Stop: `docker compose down`.

### Without Docker for the app

Python 3.11+ is needed. Only Postgres runs in Docker.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # set OPENAI_API_KEY in it
docker compose up -d db     # Postgres with pgvector
alembic upgrade head        # create the tables
uvicorn agentic_rag.api.main:app --app-dir src --reload
```

Open http://127.0.0.1:8000. Port 8000 is used, so the app container must not be running.

## Web UI

- **Documents**: upload PDFs, see the list, delete a document.
- **Search**: find the chunks with the closest meaning to a query.
- **Chat**: ask questions and get answers from the documents, with sources.
- **Status**: check if the API and the database are working.

![Documents page of the web UI](docs/agentic-rag-documents-ui.png)

![Chat page of the web UI](docs/agentic-rag-chat-ui.png)

## Quick try

```bash
curl -X POST http://127.0.0.1:8000/documents -F "file=@/path/to/file.pdf"
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" \
  -d '{"question": "What is this document about?"}'
```

All routes, responses and error codes are in [docs/api.md](docs/api.md). API docs are also at http://127.0.0.1:8000/docs.

## Settings

Settings are read from environment variables or the `.env` file (see `.env.example`).

| Name | What it is | Default |
| --- | --- | --- |
| `OPENAI_API_KEY` | API key for OpenAI, read by LiteLLM | empty |
| `LLM_MODEL` | Model for chat (any LiteLLM model that supports tool calling) | `gpt-4o-mini` |
| `EMBEDDING_MODEL` | Model for embeddings | `text-embedding-3-small` |
| `DATABASE_URL` | Postgres connection string | `postgresql+psycopg://postgres:postgres@localhost:5432/agentic_rag` |
| `UPLOAD_DIR` | Folder where uploaded files are kept | `data/uploads` |
| `CHUNK_SIZE` | Maximum characters in one chunk | `1000` |
| `CHUNK_OVERLAP` | Characters shared by two chunks next to each other | `200` |
| `AGENT_MAX_STEPS` | Maximum searches the chat agent can do before it must answer | `3` |

## Run the tests

```bash
pip install -r requirements-dev.txt
pytest
```

Unit tests need nothing. Integration tests need Postgres running (`docker compose up -d db`) and use their own `agentic_rag_test` database, so real data is not touched. LLM and embedding calls are fake in all tests.

## Docs

- [Architecture](docs/architecture.md): how the app is built and how upload, search and chat work.
- [API](docs/api.md): all routes with examples and error codes.
- [Database](docs/database.md): tables, embedding size and migration commands.

## Contributing

Please keep changes small, one thing at a time, so commit history stays easy to read. Open an issue first if the change is big.
