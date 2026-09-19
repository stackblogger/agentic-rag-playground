# Architecture

## Overview

```
Browser (web UI) --> FastAPI app --> Postgres + pgvector
                          |
                          +--> LiteLLM --> OpenAI (or any provider)
```

The web UI is plain HTML, CSS and JS, served by the same FastAPI app. LiteLLM is the only way the app talks to an LLM, so the provider can be changed from settings.

## Code layers

Code is in `src/agentic_rag/`. A layer only calls the layers below it.

- `api/`: takes the request and gives the response. No main logic here.
- `services/`: main logic of each feature.
- `agents/`: the chat agent.
- `ingestion/`: read PDF, cut text into chunks.
- `retrieval/`: the vector search query.
- `llm/`: LiteLLM calls (embeddings and chat).
- `db/`: connection and models.
- `core/`: settings.

Services raise their own errors, and the routes change them into HTTP codes (400, 404, 422, 502).

## Upload

```
POST /documents -> save file -> read text (pypdf) -> cut chunks -> make embeddings -> save in database
```

- Chunks are cut page by page, and each chunk keeps its page number.
- If the PDF cannot be read or embeddings fail, the document is saved as `failed` and no chunks are kept.

## Search

```
GET /search -> embed the query -> find nearest chunks in Postgres -> return them
```

- Closest chunks are found with cosine distance. `score` is `1 - distance`, so higher is better.
- The query must use the same embedding model as the chunks.

## Chat

```
POST /chat -> agent asks the LLM
              LLM wants to search -> run the search, give results back to the LLM (repeat)
              LLM answers         -> return answer and sources
```

- The LLM has a `search_documents` tool and decides by itself when to use it. It can search again with different words.
- It can search at most `AGENT_MAX_STEPS` times, and then it must answer.
- Each question is answered on its own. Earlier questions are not remembered.

## Delete

`DELETE /documents/{id}` removes the row and the saved file. The database removes the chunks by itself (`ON DELETE CASCADE`).

## Database and UI

- Tables are SQLAlchemy models in `db/models.py`, created by Alembic migrations. The Docker app container runs the migrations before it starts.
- Each UI page is one file in `ui/js/pages/`, and `ui/js/app.js` switches between them.
