import logging
import shutil
import time
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from agentic_rag.core.config import settings
from agentic_rag.db.models import Chunk, Document
from agentic_rag.ingestion.chunking import chunk_text
from agentic_rag.ingestion.pdf import extract_pages
from agentic_rag.llm.embeddings import embed_texts
from agentic_rag.services.errors import EmbeddingError

logger = logging.getLogger(__name__)


class InvalidFileError(Exception):
    pass


class PdfReadError(Exception):
    pass


class DocumentNotFoundError(Exception):
    pass


def save_file(file_obj: BinaryIO) -> Path:
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / f"{uuid4().hex}.pdf"
    with open(file_path, "wb") as saved_file:
        shutil.copyfileobj(file_obj, saved_file)
    return file_path


def mark_failed(db: Session, document: Document) -> None:
    document.status = "failed"
    db.add(document)
    db.commit()


def upload_document(
    db: Session, filename: str, content_type: str | None, file_obj: BinaryIO
) -> tuple[Document, int]:
    started = time.perf_counter()
    filename = Path(filename or "").name
    if not filename.lower().endswith(".pdf"):
        logger.warning("Rejected a file that is not a PDF: %s", filename)
        raise InvalidFileError("Only PDF files are allowed")

    file_path = save_file(file_obj)
    document = Document(
        filename=filename,
        file_path=str(file_path),
        content_type=content_type,
        size_bytes=file_path.stat().st_size,
    )
    logger.info("Upload started: %s (%d bytes)", filename, document.size_bytes)

    try:
        pages = extract_pages(str(file_path))
    except Exception as error:
        logger.warning("Could not read the PDF %s: %s", filename, error)
        mark_failed(db, document)
        raise PdfReadError("Could not read this PDF file")

    document.page_count = len(pages)
    document.extracted_text = "\n\n".join(pages)

    pieces = []
    for page_number, page_text in enumerate(pages, start=1):
        for piece in chunk_text(page_text, settings.chunk_size, settings.chunk_overlap):
            pieces.append((page_number, piece))
    logger.info("Read %d pages and made %d chunks from %s", len(pages), len(pieces), filename)

    try:
        vectors = embed_texts([piece for _, piece in pieces])
    except Exception:
        logger.exception("Could not create embeddings for %s", filename)
        mark_failed(db, document)
        raise EmbeddingError("Could not create embeddings")

    document.status = "processed"
    db.add(document)
    db.flush()

    for chunk_index, ((page_number, piece), vector) in enumerate(zip(pieces, vectors)):
        db.add(
            Chunk(
                document_id=document.id,
                chunk_index=chunk_index,
                page_number=page_number,
                content=piece,
                embedding=vector,
            )
        )
    db.commit()
    db.refresh(document)
    logger.info("Upload done: document_id=%s, chunks=%d, took %.1fs", document.id, len(pieces), time.perf_counter() - started)

    return document, len(pieces)


def list_documents(db: Session) -> list[tuple[Document, int]]:
    query = (
        select(Document, func.count(Chunk.id))
        .outerjoin(Chunk, Chunk.document_id == Document.id)
        .group_by(Document.id)
        .order_by(Document.id.desc())
    )
    return [(document, chunk_count) for document, chunk_count in db.execute(query).all()]


def delete_document(db: Session, document_id: int) -> None:
    document = db.get(Document, document_id)
    if document is None:
        logger.warning("Delete asked for a document that does not exist: id=%s", document_id)
        raise DocumentNotFoundError("Document not found")

    file_path = Path(document.file_path)
    filename = document.filename
    db.delete(document)
    db.commit()
    file_path.unlink(missing_ok=True)
    logger.info("Deleted document id=%s (%s)", document_id, filename)
