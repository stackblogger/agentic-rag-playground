import logging
from collections.abc import Callable
from typing import Annotated

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field
from sqlalchemy.orm import Session

from agentic_rag.db.connection import SessionLocal
from agentic_rag.db.models import Document
from agentic_rag.services import documents as document_service
from agentic_rag.services import search as search_service
from agentic_rag.services.errors import EmbeddingError

logger = logging.getLogger(__name__)


def document_to_dict(document: Document, chunk_count: int) -> dict:
    return {
        "id": document.id,
        "filename": document.filename,
        "page_count": document.page_count,
        "chunk_count": chunk_count,
        "size_bytes": document.size_bytes,
        "status": document.status,
        "created_at": document.created_at.isoformat(),
    }


def create_server(session_factory: Callable[[], Session] = SessionLocal) -> MCPServer:
    server = MCPServer("agentic-rag")

    @server.tool()
    def list_documents() -> list[dict]:
        """List the uploaded documents, newest first.

        Each item has id, filename, page_count, chunk_count, size_bytes, status
        ("processed" or "failed") and created_at.
        """
        db = session_factory()
        try:
            documents = document_service.list_documents(db)
            logger.info("MCP list_documents: %d documents", len(documents))
            return [document_to_dict(document, chunk_count) for document, chunk_count in documents]
        finally:
            db.close()

    @server.tool()
    def search_documents(
        query: Annotated[str, Field(min_length=1, description="What to look for, in plain words")],
        limit: Annotated[int, Field(ge=1, le=20, description="How many chunks to return")] = 5,
    ) -> list[dict]:
        """Search the uploaded documents by meaning.

        Returns the best matching chunks, best first. Each item has chunk_id,
        document_id, filename, page_number, content and score (higher is better).
        """
        db = session_factory()
        try:
            return search_service.search_documents(db, query, limit)
        except EmbeddingError as error:
            # only a ToolError keeps its message for the client
            raise ToolError(str(error))
        finally:
            db.close()

    return server
