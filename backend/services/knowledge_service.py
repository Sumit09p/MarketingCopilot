from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bson import ObjectId

from database import get_database
from knowledge.ingestion import DocumentIngestionService
from rag.retriever import SemanticRetriever


DOCUMENTS_COLLECTION = "documents"
KNOWLEDGE_CHUNKS_COLLECTION = "knowledge_chunks"

RAG_STORAGE_ROOT = Path("data") / "rag"


class KnowledgeService:
    """
    Per-user knowledge management service.

    Each user receives an isolated FAISS index.
    MongoDB stores document metadata and extracted chunks.
    """

    def __init__(self) -> None:
        database = get_database()

        self.documents = database[DOCUMENTS_COLLECTION]
        self.knowledge_chunks = database[KNOWLEDGE_CHUNKS_COLLECTION]

    # ------------------------------------------------------------------
    # Per-user RAG
    # ------------------------------------------------------------------

    def _get_storage_path(self, user_id: str) -> Path:
        user_id = str(user_id).strip()

        if not user_id:
            raise ValueError("user_id is required.")

        path = RAG_STORAGE_ROOT / user_id
        path.mkdir(parents=True, exist_ok=True)

        return path

    def _build_ingestion_service(
        self,
        user_id: str,
    ) -> DocumentIngestionService:
        """
        Create a fresh retriever for one user.

        The user's FAISS index is loaded from that user's directory
        when it already exists.
        """

        storage_path = self._get_storage_path(user_id)

        retriever = SemanticRetriever()

        ingestion = DocumentIngestionService(
            retriever=retriever,
        )

        index_file = storage_path / "index.faiss"
        metadata_file = storage_path / "metadata.json"

        if index_file.exists() and metadata_file.exists():
            ingestion.load_index(storage_path)

        return ingestion

    # ------------------------------------------------------------------
    # Document ingestion
    # ------------------------------------------------------------------

    def ingest_document(
        self,
        *,
        user_id: str,
        file_path: str | Path,
        filename: str,
    ) -> dict[str, Any]:
        """
        Extract and index a document for one user.
        """

        ingestion = self._build_ingestion_service(user_id)

        result = ingestion.ingest_file(
            file_path=file_path,
            source=filename,
        )

        storage_path = self._get_storage_path(user_id)

        ingestion.save_index(storage_path)

        return result

    # ------------------------------------------------------------------
    # MongoDB document metadata
    # ------------------------------------------------------------------

    def create_document_record(
        self,
        *,
        user_id: str,
        filename: str,
        source: str,
        extension: str,
        characters: int,
        chunks_created: int,
    ) -> dict[str, Any]:

        now = datetime.now(UTC)

        document = {
            "user_id": str(user_id),
            "filename": filename,
            "source": source,
            "extension": extension,
            "characters": characters,
            "chunks_created": chunks_created,
            "status": "INDEXED",
            "created_at": now,
            "updated_at": now,
        }

        result = self.documents.insert_one(document)

        document["_id"] = result.inserted_id

        return self._document_to_response(document)

    def list_documents(
        self,
        user_id: str,
    ) -> list[dict[str, Any]]:

        documents = self.documents.find(
            {
                "user_id": str(user_id),
            }
        ).sort(
            "created_at",
            -1,
        )

        return [
            self._document_to_response(document)
            for document in documents
        ]

    def get_document(
        self,
        user_id: str,
        document_id: str,
    ) -> dict[str, Any] | None:

        try:
            object_id = ObjectId(document_id)
        except Exception:
            return None

        document = self.documents.find_one(
            {
                "_id": object_id,
                "user_id": str(user_id),
            }
        )

        if document is None:
            return None

        return self._document_to_response(document)

    # ------------------------------------------------------------------
    # MongoDB chunks
    # ------------------------------------------------------------------

    def store_chunks(
        self,
        *,
        user_id: str,
        document_id: str,
        chunks: list[dict[str, Any]],
    ) -> int:

        if not chunks:
            return 0

        now = datetime.now(UTC)

        records = []

        for chunk in chunks:
            records.append(
                {
                    "user_id": str(user_id),
                    "document_id": str(document_id),
                    "chunk_id": chunk.get("chunk_id"),
                    "source": chunk.get("source"),
                    "text": chunk.get("text", ""),
                    "score": chunk.get("score"),
                    "created_at": now,
                }
            )

        self.knowledge_chunks.insert_many(records)

        return len(records)

    # ------------------------------------------------------------------
    # Semantic search
    # ------------------------------------------------------------------

    def search(
        self,
        *,
        user_id: str,
        query: str,
        top_k: int = 3,
        min_score: float = 0.0,
    ) -> list[dict[str, Any]]:

        if not query or not query.strip():
            raise ValueError("query is required.")

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than 0."
            )

        if not 0.0 <= min_score <= 1.0:
            raise ValueError(
                "min_score must be between 0.0 and 1.0."
            )

        storage_path = self._get_storage_path(user_id)

        index_file = storage_path / "index.faiss"
        metadata_file = storage_path / "metadata.json"

        if not index_file.exists() or not metadata_file.exists():
            return []

        ingestion = self._build_ingestion_service(user_id)

        return ingestion.search(
            query=query,
            top_k=top_k,
            min_score=min_score,
        )

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def get_stats(
        self,
        user_id: str,
    ) -> dict[str, int]:

        document_count = self.documents.count_documents(
            {
                "user_id": str(user_id),
            }
        )

        chunk_count = self.knowledge_chunks.count_documents(
            {
                "user_id": str(user_id),
            }
        )

        return {
            "documents": document_count,
            "chunks": chunk_count,
        }

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    @staticmethod
    def _document_to_response(
        document: dict[str, Any],
    ) -> dict[str, Any]:

        return {
            "id": str(document["_id"]),
            "user_id": document["user_id"],
            "filename": document["filename"],
            "source": document["source"],
            "extension": document["extension"],
            "characters": document["characters"],
            "chunks_created": document["chunks_created"],
            "status": document["status"],
            "created_at": document["created_at"],
            "updated_at": document["updated_at"],
        }