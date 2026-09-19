# Agentic RAG Playground

A simple playground for developers to try Agentic RAG. You upload your documents, then you can chat with them or search inside them.

## What is this?

RAG means "Retrieval Augmented Generation". In simple words: we first find the useful parts from your documents, then we give those parts to the LLM so it can answer properly.

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

3. Start the app

   ```bash
   uvicorn agentic_rag.api.main:app --app-dir src --reload
   ```

4. Check that it is running. Open http://127.0.0.1:8000/health and you should see `{"status": "ok"}`. API docs are at http://127.0.0.1:8000/docs.

## Contributing

Please keep changes small, one thing at a time, so commit history stays easy to read. Open an issue first if you want to do something big.
