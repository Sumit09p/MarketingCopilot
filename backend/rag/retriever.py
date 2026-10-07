from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


@dataclass
class RetrievedChunk:
    source: str
    text: str
    score: float
    chunk_id: int

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "text": self.text,
            "score": self.score,
            "chunk_id": self.chunk_id,
        }


class SemanticRetriever:
    """
    Production-oriented local semantic RAG retriever.

    Features:
    - Sentence Transformer embeddings
    - FAISS vector similarity search
    - Document chunking with overlap
    - Source metadata
    - Similarity threshold filtering
    - Save/load index for persistence
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        chunk_size: int = 120,
        chunk_overlap: int = 30,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero.")

        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative.")

        if chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap must be smaller than chunk_size."
            )

        self.model = SentenceTransformer(model_name)

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        self._chunks: list[RetrievedChunk] = []

        dimension = self.model.get_embedding_dimension()

        # Inner product on normalized vectors = cosine similarity.
        self._index = faiss.IndexFlatIP(dimension)

    @property
    def chunk_count(self) -> int:
        """Return the number of indexed chunks."""
        return len(self._chunks)

    def _chunk_text(self, text: str) -> list[str]:
        """
        Split a document into overlapping word-based chunks.
        """

        words = text.split()

        if not words:
            return []

        chunks: list[str] = []

        start = 0
        step = self.chunk_size - self.chunk_overlap

        while start < len(words):
            end = min(start + self.chunk_size, len(words))

            chunk = " ".join(words[start:end]).strip()

            if chunk:
                chunks.append(chunk)

            if end >= len(words):
                break

            start += step

        return chunks

    def add_document(
        self,
        source: str,
        text: str,
    ) -> int:
        """
        Chunk and index a document.

        Returns the number of chunks created.
        """

        if not source or not str(source).strip():
            raise ValueError("Document source is required.")

        if text is None or not str(text).strip():
            raise ValueError("Document text is required.")

        source = str(source).strip()
        text = str(text).strip()

        chunks = self._chunk_text(text)

        if not chunks:
            return 0

        embeddings = self.model.encode(
            chunks,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype("float32")

        start_chunk_id = len(self._chunks)

        self._index.add(embeddings)

        for offset, chunk_text in enumerate(chunks):
            self._chunks.append(
                RetrievedChunk(
                    source=source,
                    text=chunk_text,
                    score=0.0,
                    chunk_id=start_chunk_id + offset,
                )
            )

        return len(chunks)

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        min_score: float = 0.0,
    ) -> list[dict]:
        """
        Retrieve the most semantically relevant chunks.
        """

        if query is None or not str(query).strip():
            return []

        if top_k <= 0:
            return []

        if not self._chunks:
            return []

        if min_score < -1.0 or min_score > 1.0:
            raise ValueError("min_score must be between -1.0 and 1.0.")

        query_embedding = self.model.encode(
            [str(query).strip()],
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype("float32")

        k = min(top_k, len(self._chunks))

        scores, indices = self._index.search(
            query_embedding,
            k,
        )

        results: list[dict] = []

        for score, index in zip(scores[0], indices[0]):
            if index < 0:
                continue

            score = float(score)

            if score < min_score:
                continue

            chunk = self._chunks[index]

            results.append(
                RetrievedChunk(
                    source=chunk.source,
                    text=chunk.text,
                    score=score,
                    chunk_id=chunk.chunk_id,
                ).as_dict()
            )

        return results

    def save(self, directory: str | Path) -> None:
        """
        Persist the FAISS index and chunk metadata.
        """

        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        faiss.write_index(
            self._index,
            str(directory / "index.faiss"),
        )

        metadata = [
            {
                "source": chunk.source,
                "text": chunk.text,
                "chunk_id": chunk.chunk_id,
            }
            for chunk in self._chunks
        ]

        with open(
            directory / "metadata.json",
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                metadata,
                file,
                ensure_ascii=False,
                indent=2,
            )

    def load(self, directory: str | Path) -> None:
        """
        Load a previously persisted FAISS index and metadata.
        """

        directory = Path(directory)

        index_path = directory / "index.faiss"
        metadata_path = directory / "metadata.json"

        if not index_path.exists():
            raise FileNotFoundError(
                f"FAISS index not found: {index_path}"
            )

        if not metadata_path.exists():
            raise FileNotFoundError(
                f"Metadata file not found: {metadata_path}"
            )

        self._index = faiss.read_index(
            str(index_path)
        )

        with open(
            metadata_path,
            "r",
            encoding="utf-8",
        ) as file:
            metadata = json.load(file)

        self._chunks = [
            RetrievedChunk(
                source=item["source"],
                text=item["text"],
                score=0.0,
                chunk_id=int(item["chunk_id"]),
            )
            for item in metadata
        ]
