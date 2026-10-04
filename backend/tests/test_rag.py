from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from rag.retriever import SemanticRetriever
from knowledge.ingestion import DocumentIngestionService


class FakeModel:
    """
    Lightweight embedding model used for deterministic tests.
    """

    def get_embedding_dimension(self) -> int:
        return 4

    def encode(
        self,
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ):
        vectors = []

        for text in texts:
            value = str(text).lower()

            vector = np.array(
                [
                    value.count("marketing"),
                    value.count("seo"),
                    value.count("content"),
                    value.count("finance"),
                ],
                dtype="float32",
            )

            if np.linalg.norm(vector) == 0:
                vector[0] = 1.0

            if normalize_embeddings:
                vector = vector / np.linalg.norm(vector)

            vectors.append(vector)

        return np.array(vectors, dtype="float32")


class TestSemanticRetriever(unittest.TestCase):

    def create_retriever(self):
        with patch(
            "rag.retriever.SentenceTransformer",
            return_value=FakeModel(),
        ):
            retriever = SemanticRetriever(
                chunk_size=20,
                chunk_overlap=5,
            )

        return retriever

    def test_add_document_creates_chunks(self):
        retriever = self.create_retriever()

        text = (
            "Marketing strategy and SEO optimization. "
            "Content marketing improves brand visibility."
        )

        count = retriever.add_document(
            source="test.txt",
            text=text,
        )

        self.assertGreater(count, 0)
        self.assertEqual(
            retriever.chunk_count,
            count,
        )

    def test_empty_document_is_rejected(self):
        retriever = self.create_retriever()

        with self.assertRaises(ValueError):
            retriever.add_document(
                source="test.txt",
                text="",
            )

    def test_retrieval_returns_relevant_chunks(self):
        retriever = self.create_retriever()

        retriever.add_document(
            source="marketing.txt",
            text=(
                "Marketing strategy and content marketing "
                "for modern businesses."
            ),
        )

        retriever.add_document(
            source="finance.txt",
            text=(
                "Finance and investment planning "
                "for personal wealth."
            ),
        )

        results = retriever.retrieve(
            query="marketing content",
            top_k=2,
        )

        self.assertGreater(
            len(results),
            0,
        )

        self.assertEqual(
            results[0]["source"],
            "marketing.txt",
        )

    def test_top_k_limits_results(self):
        retriever = self.create_retriever()

        retriever.add_document(
            source="one.txt",
            text="marketing content",
        )

        retriever.add_document(
            source="two.txt",
            text="marketing strategy",
        )

        results = retriever.retrieve(
            query="marketing",
            top_k=1,
        )

        self.assertEqual(
            len(results),
            1,
        )

    def test_invalid_similarity_threshold_is_rejected(self):
        retriever = self.create_retriever()

        retriever.add_document(
            source="test.txt",
            text="marketing content",
        )

        with self.assertRaises(ValueError):
            retriever.retrieve(
                query="marketing",
                min_score=2.0,
            )

    def test_save_and_load_preserves_index(self):
        retriever = self.create_retriever()

        retriever.add_document(
            source="marketing.txt",
            text=(
                "Marketing content and SEO strategy "
                "for businesses."
            ),
        )

        with tempfile.TemporaryDirectory() as directory:

            retriever.save(directory)

            loaded = self.create_retriever()
            loaded.load(directory)

            self.assertEqual(
                loaded.chunk_count,
                retriever.chunk_count,
            )

            results = loaded.retrieve(
                query="marketing SEO",
                top_k=1,
            )

            self.assertGreater(
                len(results),
                0,
            )


class TestDocumentIngestionService(unittest.TestCase):

    def test_txt_ingestion(self):
        retriever = unittest.mock.Mock()

        service = DocumentIngestionService(
            retriever=retriever,
        )

        with tempfile.TemporaryDirectory() as directory:

            path = Path(directory) / "brand.txt"

            path.write_text(
                "Our company provides digital marketing services.",
                encoding="utf-8",
            )

            retriever.add_document.return_value = 2

            result = service.ingest_file(path)

            self.assertEqual(
                result["status"],
                "INDEXED",
            )

            self.assertEqual(
                result["extension"],
                ".txt",
            )

            self.assertEqual(
                result["chunks_created"],
                2,
            )

            retriever.add_document.assert_called_once()

    def test_unsupported_file_is_rejected(self):
        retriever = unittest.mock.Mock()

        service = DocumentIngestionService(
            retriever=retriever,
        )

        with tempfile.TemporaryDirectory() as directory:

            path = Path(directory) / "test.csv"

            path.write_text(
                "name,value",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                service.ingest_file(path)

    def test_missing_file_is_rejected(self):
        retriever = unittest.mock.Mock()

        service = DocumentIngestionService(
            retriever=retriever,
        )

        with self.assertRaises(FileNotFoundError):
            service.ingest_file(
                "does-not-exist.txt"
            )


if __name__ == "__main__":
    unittest.main()