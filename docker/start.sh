#!/bin/sh
set -e

# make the tables first, then start the app
alembic upgrade head
exec uvicorn agentic_rag.api.main:app --app-dir src --host 0.0.0.0 --port 8000
