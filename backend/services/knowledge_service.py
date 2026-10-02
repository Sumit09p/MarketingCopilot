from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bson import ObjectId

from database import get_database
from knowledge.ingestion import DocumentIngestionService


DOCUMENTS_COLLECTION = "documents"
KNOWLEDGE_CHUNKS_COLLECTION = "knowledge_chunks"

RAG_STORAGE_ROOT = Path("data") / "rag"


class KnowledgeService:
    """
    Per-user knowledge management service.

    Responsibilities:
    - Store document metadata in MongoDB
    - Extract and index document content
    - Search a user's knowledge base
    - Keep each user's RAG index isolated
    """

    def __init__(
        self,
        ingestion_service: DocumentIngestionService | None = None,
    ) -> None:
        database = get_database()

        self.documents = database[DOCUMENTS_COLLECTION]
        self.knowledge_chunks = database[KNOWLEDGE_CHUNKS_COLLECTION]

        self.ingestion_service = ingestion_service

    # ------------------------------------------------------------------
    # Storage
    # ------------------------------------------------------------------

    def _get_storage_path(self, user_id: str) -> Path:
        """Return the isolated FAISS directory for one user."""
        safe_user_id = str(user_id).strip()

        if not safe_user_id:
            raise ValueError("user_id is required.")

        path = RAG_STORAGE_ROOT / safe_user_id
        path.mkdir(parents=True, exist_ok=True)

        return path

    def _get_ingestion_service(self) -> DocumentIngestionService:
        """
        Lazily create the ingestion service.

        This keeps the service easy to test because a fake ingestion
        service can be injected through the constructor.
        """
        if self.ingestion_service is None:
            storage = self._get_storage_path("global")
            self.ingestion_service = DocumentIngestionService()

        return self.ingestion_service

    # ------------------------------------------------------------------
    # Documents
    # ------------------------------------------------------------------

    def list_documents(self, user_id: str) -> list[dict[str, Any]]:
        """Return all documents belonging to a user."""

        documents = self.documents.find(
            {"user_id": str(user_id)}
        ).sort("created_at", -1)

        return [
            self._document_to_response(document)
            for document in documents
        ]

    def get_document(
        self,
        user_id: str,
        document_id: str,
    ) -> dict[str, Any] | None:
        """Return one document owned by the user."""

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
        """Persist document metadata after successful ingestion."""

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

    # ------------------------------------------------------------------
    # Knowledge chunks
    # ------------------------------------------------------------------

    def store_chunks(
        self,
        *,
        user_id: str,
        document_id: str,
        chunks: list[dict[str, Any]],
    ) -> int:
        """
        Persist extracted chunks in MongoDB.

        The FAISS index is used for semantic retrieval, while MongoDB
        keeps a durable representation of the knowledge chunks.
        """

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

        if not records:
            return 0

        self.knowledge_chunks.insert_many(records)

        return len(records)

    def search(
        self,
        *,
        user_id: str,
        query: str,
        top_k: int = 3,
        min_score: float = 0.0,
    ) -> list[dict[str, Any]]:
        """
        Search the user's knowledge base.

        Each user gets an isolated RAG index.
        """

        if not query or not query.strip():
            raise ValueError("query is required.")

        if top_k <= 0:
            raise ValueError("top_k must be greater than 0.")

        if not 0.0 <= min_score <= 1.0:
            raise ValueError(
                "min_score must be between 0.0 and 1.0."
            )

        storage_path = self._get_storage_path(user_id)

        index_file = storage_path / "index.faiss"
        metadata_file = storage_path / "metadata.json"

        if not index_file.exists() or not metadata_file.exists():
            return []

        ingestion = self._get_ingestion_service()

        ingestion.load_index(storage_path)

        return ingestion.search(
            query=query,
            top_k=top_k,
            min_score=min_score,
        )

    # ------------------------------------------------------------------
    # Index management
    # ------------------------------------------------------------------

    def save_user_index(self, user_id: str) -> None:
        """Persist the user's FAISS index."""

        storage_path = self._get_storage_path(user_id)

        ingestion = self._get_ingestion_service()

        ingestion.save_index(storage_path)

    def load_user_index(self, user_id: str) -> None:
        """Load a user's FAISS index if it exists."""

        storage_path = self._get_storage_path(user_id)

        index_file = storage_path / "index.faiss"
        metadata_file = storage_path / "metadata.json"

        if not index_file.exists() or not metadata_file.exists():
            return

        ingestion = self._get_ingestion_service()

        ingestion.load_index(storage_path)

    def get_stats(self, user_id: str) -> dict[str, int]:
        """Return knowledge statistics for a user."""

        document_count = self.documents.count_documents(
            {"user_id": str(user_id)}
        )

        chunk_count = self.knowledge_chunks.count_documents(
            {"user_id": str(user_id)}
        )

        return {
            "documents": document_count,
            "chunks": chunk_count,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _document_to_response(
        document: dict[str, Any],
    ) -> dict[str, Any]:
        """Convert MongoDB document into API-safe response."""

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