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
- Docker Compose (to run Postgres locally)

## Folder structure

```
agentic-rag-playground/
├── src/agentic_rag/
│   ├── api/          # API routes (upload, search, chat)
│   ├── core/         # config, settings, logging
│   ├── db/           # database connection and models
│   ├── ingestion/    # read file, extract text, make chunks
│   ├── retrieval/    # embeddings and search logic
│   ├── agents/       # agent logic, decides what to search and when
│   └── llm/          # LiteLLM wrapper
├── migrations/       # database migration files
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

5. Start the app

   ```bash
   uvicorn agentic_rag.api.main:app --app-dir src --reload
   ```

6. Check that it is running. Open http://127.0.0.1:8000/health and it should show `{"status": "ok"}`. API docs are at http://127.0.0.1:8000/docs.

## Settings

All settings are read from environment variables or the `.env` file (see `.env.example`).

| Name | What it is | Default |
| --- | --- | --- |
| `DATABASE_URL` | Postgres connection string | `postgresql://postgres:postgres@localhost:5432/agentic_rag` |
| `UPLOAD_DIR` | Folder where uploaded files are kept | `data/uploads` |
| `LLM_MODEL` | Model name used for chat (any LiteLLM model) | `gpt-4o-mini` |
| `EMBEDDING_MODEL` | Model name used for embeddings | `text-embedding-3-small` |

The app runs on the local machine and Postgres runs inside Docker, so the host in `DATABASE_URL` must be `localhost`. The container name `agentic-rag-db` only works from another container in the same Docker network.

## Contributing

Please keep changes small, one thing at a time, so commit history stays easy to read. Open an issue first if the change is big.
