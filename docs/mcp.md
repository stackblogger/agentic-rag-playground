# MCP server

The app has a small MCP server. MCP clients like Claude Desktop, Claude Code and Cursor can use it to search the uploaded documents and list them, without the web UI.

It is read-only. It has no tool to upload or delete documents. It runs on the same machine as the client (stdio), and the client starts it.

## Tools

| Tool | What it does |
| --- | --- |
| `list_documents` | Lists the uploaded documents, newest first |
| `search_documents` | Searches the chunks by meaning |

### list_documents

No arguments. Returns a list. Each item has `id`, `filename`, `page_count`, `chunk_count`, `size_bytes`, `status` (`processed` or `failed`) and `created_at`. An empty list means nothing is uploaded.

### search_documents

| Argument | What it is |
| --- | --- |
| `query` | What to look for. It cannot be empty. |
| `limit` | How many chunks to return, from 1 to 20 (default 5) |

Returns a list of chunks, best first. Each item has `chunk_id`, `document_id`, `filename`, `page_number`, `content` and `score`. It is the same search as `GET /search` in [API](api.md), so the results are reranked too when `RERANK_ENABLED` is on.

Errors: an empty query or a `limit` outside 1 to 20 is refused, and `Could not create embeddings` is returned if the embedding call fails.

## Run it

Postgres must be running, and the packages must be installed (see the README).

```bash
PYTHONPATH=src python -m agentic_rag.mcp_server
```

The server waits for a client on stdin and stdout, so nothing is shown in the terminal. Logs go to stderr, and stdout is only for the MCP protocol.

Settings are the same as the API (see the README). The `.env` file is only read when the server starts inside the project folder. A client usually starts it from another folder, so pass the settings as environment variables in the client config, as in the examples below.

## Try it in the MCP Inspector

The MCP Inspector is a browser page to call the tools by hand. Run this from the project folder, with Postgres running:

```bash
npx @modelcontextprotocol/inspector -e PYTHONPATH=$PWD/src .venv/bin/python -m agentic_rag.mcp_server
```

Open the address it prints, press Connect, and use the Tools tab. `PYTHONPATH` is passed with `-e` because the Inspector starts the server as a separate process.

## Connect a client

Use the full path of the project folder and of the Python that has the packages installed (for example `.venv/bin/python`). `DATABASE_URL` is the one from `.env.example` when Postgres runs with `docker compose up -d db`.

### Claude Desktop

Add this to `claude_desktop_config.json`, then restart Claude Desktop:

```json
{
  "mcpServers": {
    "agentic-rag": {
      "command": "/path/to/agentic-rag-playground/.venv/bin/python",
      "args": ["-m", "agentic_rag.mcp_server"],
      "env": {
        "PYTHONPATH": "/path/to/agentic-rag-playground/src",
        "DATABASE_URL": "postgresql+psycopg://postgres:postgres@localhost:5432/agentic_rag",
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

### Claude Code

```bash
claude mcp add agentic-rag \
  -e PYTHONPATH=/path/to/agentic-rag-playground/src \
  -e DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/agentic_rag \
  -e OPENAI_API_KEY=sk-... \
  -- /path/to/agentic-rag-playground/.venv/bin/python -m agentic_rag.mcp_server
```

`OPENAI_API_KEY` is needed because every search makes an embedding of the query. If another provider is used through LiteLLM, pass its key and `EMBEDDING_MODEL` instead.
