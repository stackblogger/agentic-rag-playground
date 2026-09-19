import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from agentic_rag.core.config import settings
from agentic_rag.db.connection import get_db
from agentic_rag.db.models import Chunk, Document
from agentic_rag.ingestion.chunking import chunk_text
from agentic_rag.ingestion.pdf import extract_pages

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", status_code=201)
def upload_document(file: UploadFile, db: Session = Depends(get_db)):
    filename = Path(file.filename or "").name
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / f"{uuid4().hex}.pdf"
    with open(file_path, "wb") as saved_file:
        shutil.copyfileobj(file.file, saved_file)

    document = Document(
        filename=filename,
        file_path=str(file_path),
        content_type=file.content_type,
        size_bytes=file_path.stat().st_size,
    )

    try:
        pages = extract_pages(str(file_path))
    except Exception:
        document.status = "failed"
        db.add(document)
        db.commit()
        raise HTTPException(status_code=422, detail="Could not read this PDF file")

    document.page_count = len(pages)
    document.extracted_text = "\n\n".join(pages)
    document.status = "processed"
    db.add(document)
    db.flush()

    chunk_count = 0
    for page_number, page_text in enumerate(pages, start=1):
        for piece in chunk_text(page_text, settings.chunk_size, settings.chunk_overlap):
            db.add(
                Chunk(
                    document_id=document.id,
                    chunk_index=chunk_count,
                    page_number=page_number,
                    content=piece,
                )
            )
            chunk_count += 1
    db.commit()
    db.refresh(document)

    return {
        "id": document.id,
        "filename": document.filename,
        "page_count": document.page_count,
        "chunk_count": chunk_count,
        "status": document.status,
    }
