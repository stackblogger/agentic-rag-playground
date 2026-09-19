import shutil
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
    filename = Path(filename or "").name
    if not filename.lower().endswith(".pdf"):
        raise InvalidFileError("Only PDF files are allowed")

    file_path = save_file(file_obj)
    document = Document(
        filename=filename,
        file_path=str(file_path),
        content_type=content_type,
        size_bytes=file_path.stat().st_size,
    )

    try:
        pages = extract_pages(str(file_path))
    except Exception:
        mark_failed(db, document)
        raise PdfReadError("Could not read this PDF file")

    document.page_count = len(pages)
    document.extracted_text = "\n\n".join(pages)

    pieces = []
    for page_number, page_text in enumerate(pages, start=1):
        for piece in chunk_text(page_text, settings.chunk_size, settings.chunk_overlap):
            pieces.append((page_number, piece))

    try:
        vectors = embed_texts([piece for _, piece in pieces])
    except Exception:
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
        raise DocumentNotFoundError("Document not found")

    file_path = Path(document.file_path)
    db.delete(document)
    db.commit()
    file_path.unlink(missing_ok=True)
