from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from agentic_rag.db.connection import get_db
from agentic_rag.services import documents as document_service
from agentic_rag.services.errors import EmbeddingError

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", status_code=201)
def upload_document(file: UploadFile, db: Session = Depends(get_db)):
    try:
        document, chunk_count = document_service.upload_document(
            db, file.filename, file.content_type, file.file
        )
    except document_service.InvalidFileError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except document_service.PdfReadError as error:
        raise HTTPException(status_code=422, detail=str(error))
    except EmbeddingError as error:
        raise HTTPException(status_code=502, detail=str(error))

    return {
        "id": document.id,
        "filename": document.filename,
        "page_count": document.page_count,
        "chunk_count": chunk_count,
        "status": document.status,
    }
