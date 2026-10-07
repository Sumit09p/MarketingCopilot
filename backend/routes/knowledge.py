from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from backend.schemas.knowledge import (
    KnowledgeDocumentResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSearchResult,
    KnowledgeStatsResponse,
)
from backend.services.knowledge_service import KnowledgeService
from backend.utils.auth import get_current_user


router = APIRouter(
    prefix="/api/knowledge",
    tags=["Knowledge"],
)


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt",
}


def get_knowledge_service() -> KnowledgeService:
    return KnowledgeService()


@router.post(
    "/upload",
    response_model=KnowledgeDocumentResponse,
)
async def upload_knowledge_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    knowledge_service: KnowledgeService = Depends(
        get_knowledge_service
    ),
):
    """
    Upload a PDF, DOCX, or TXT document
    into the current user's knowledge base.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    filename = Path(file.filename).name
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Only PDF, DOCX, and TXT files "
                "are supported."
            ),
        )

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    temporary_path: Path | None = None

    try:
        with NamedTemporaryFile(
            suffix=extension,
            delete=False,
        ) as temporary_file:
            temporary_file.write(file_bytes)
            temporary_path = Path(
                temporary_file.name
            )

        ingestion_result = (
            knowledge_service.ingest_document(
                user_id=str(current_user["_id"]),
                file_path=temporary_path,
                filename=filename,
            )
        )

        document = (
            knowledge_service.create_document_record(
                user_id=str(current_user["_id"]),
                filename=filename,
                source=ingestion_result["source"],
                extension=ingestion_result["extension"],
                characters=ingestion_result["characters"],
                chunks_created=ingestion_result[
                    "chunks_created"
                ],
            )
        )

        return document

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Knowledge ingestion failed: {exc}"
            ),
        ) from exc

    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(
                    missing_ok=True
                )
            except OSError:
                pass


@router.get(
    "/documents",
    response_model=list[KnowledgeDocumentResponse],
)
def list_knowledge_documents(
    current_user: dict = Depends(get_current_user),
    knowledge_service: KnowledgeService = Depends(
        get_knowledge_service
    ),
):
    """Return documents belonging to the current user."""

    return knowledge_service.list_documents(
        str(current_user["_id"])
    )


@router.post(
    "/search",
    response_model=KnowledgeSearchResponse,
)
def search_knowledge(
    request: KnowledgeSearchRequest,
    current_user: dict = Depends(get_current_user),
    knowledge_service: KnowledgeService = Depends(
        get_knowledge_service
    ),
):
    """Perform semantic search over the user's knowledge."""

    try:
        results = knowledge_service.search(
            user_id=str(current_user["_id"]),
            query=request.query,
            top_k=request.top_k,
            min_score=request.min_score,
        )

        return KnowledgeSearchResponse(
            query=request.query,
            results=[
                KnowledgeSearchResult(
                    source=result["source"],
                    text=result["text"],
                    score=float(result["score"]),
                    chunk_id=result.get("chunk_id"),
                )
                for result in results
            ],
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Knowledge search failed: {exc}"
            ),
        ) from exc


@router.get(
    "/stats",
    response_model=KnowledgeStatsResponse,
)
def knowledge_stats(
    current_user: dict = Depends(get_current_user),
    knowledge_service: KnowledgeService = Depends(
        get_knowledge_service
    ),
):
    """Return knowledge-base statistics."""

    return knowledge_service.get_stats(
        str(current_user["_id"])
    )
