from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from services.knowledge_service import KnowledgeService


class FakeCursor:
    def __init__(self, documents):
        self.documents = documents

    def sort(self, *_args, **_kwargs):
        return self.documents


class FakeCollection:
    def __init__(self):
        self.documents = []

    def insert_one(self, document):
        document = dict(document)
        document["_id"] = "fake-document-id"
        self.documents.append(document)

        class Result:
            inserted_id = "fake-document-id"

        return Result()

    def find(self, query):
        matching = [
            document
            for document in self.documents
            if document.get("user_id") == query.get("user_id")
        ]

        return FakeCursor(matching)

    def find_one(self, query):
        for document in self.documents:
            if document.get("user_id") != query.get("user_id"):
                continue

            if "_id" in query:
                if document.get("_id") == query["_id"]:
                    return document
            else:
                return document

        return None

    def count_documents(self, query):
        return sum(
            1
            for document in self.documents
            if document.get("user_id") == query.get("user_id")
        )


class FakeDatabase:
    def __init__(self):
        self.collections = {
            "documents": FakeCollection(),
            "knowledge_chunks": FakeCollection(),
        }

    def __getitem__(self, name):
        return self.collections[name]


class FakeRetriever:
    def __init__(self):
        self.documents = []

    def add_document(self, source, text):
        self.documents.append(
            {
                "source": source,
                "text": text,
            }
        )

        return 1

    def retrieve(
        self,
        query,
        top_k=3,
        min_score=0.0,
    ):
        if not self.documents:
            return []

        return [
            {
                "source": item["source"],
                "text": item["text"],
                "score": 0.95,
                "chunk_id": 0,
            }
            for item in self.documents[:top_k]
        ]

    def save(self, directory):
        directory = Path(directory)
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        # Only create marker files for the fake test.
        # Real FAISS persistence is tested elsewhere.
        (directory / "index.faiss").write_bytes(
            b"fake-index"
        )

        (directory / "metadata.json").write_text(
            "{}",
            encoding="utf-8",
        )

    def load(self, directory):
        return None


class FakeIngestionService:
    def __init__(self, retriever=None):
        self.retriever = (
            retriever or FakeRetriever()
        )

    def ingest_file(
        self,
        file_path,
        source=None,
    ):
        path = Path(file_path)

        text = path.read_text(
            encoding="utf-8"
        )

        chunks = self.retriever.add_document(
            source=source or path.name,
            text=text,
        )

        return {
            "source": source or path.name,
            "filename": path.name,
            "extension": path.suffix.lower(),
            "characters": len(text),
            "chunks_created": chunks,
            "status": "INDEXED",
        }

    def save_index(self, directory):
        self.retriever.save(directory)

    def search(
        self,
        query,
        top_k=3,
        min_score=0.0,
    ):
        return self.retriever.retrieve(
            query=query,
            top_k=top_k,
            min_score=min_score,
        )

    def load_index(self, directory):
        return None


class TestKnowledgeService(unittest.TestCase):

    def setUp(self):
        self.database = FakeDatabase()

        self.database_patch = patch(
            "services.knowledge_service.get_database",
            return_value=self.database,
        )

        self.database_patch.start()

        self.temp_dir = tempfile.mkdtemp()

        self.service = KnowledgeService()

    def tearDown(self):
        self.database_patch.stop()

        shutil.rmtree(
            self.temp_dir,
            ignore_errors=True,
        )

    def test_create_document_record(self):
        result = self.service.create_document_record(
            user_id="user-1",
            filename="brand.txt",
            source="brand.txt",
            extension=".txt",
            characters=100,
            chunks_created=2,
        )

        self.assertEqual(
            result["user_id"],
            "user-1",
        )

        self.assertEqual(
            result["filename"],
            "brand.txt",
        )

        self.assertEqual(
            result["chunks_created"],
            2,
        )

    def test_list_documents_is_user_specific(self):
        self.service.create_document_record(
            user_id="user-1",
            filename="brand-a.txt",
            source="brand-a.txt",
            extension=".txt",
            characters=100,
            chunks_created=2,
        )

        self.service.create_document_record(
            user_id="user-2",
            filename="brand-b.txt",
            source="brand-b.txt",
            extension=".txt",
            characters=200,
            chunks_created=3,
        )

        user_one_documents = (
            self.service.list_documents(
                "user-1"
            )
        )

        self.assertEqual(
            len(user_one_documents),
            1,
        )

        self.assertEqual(
            user_one_documents[0]["filename"],
            "brand-a.txt",
        )

    def test_search_requires_query(self):
        with self.assertRaises(ValueError):
            self.service.search(
                user_id="user-1",
                query="",
            )

    def test_search_returns_empty_when_index_missing(self):
        # Prevent the real SemanticRetriever from being
        # created for this unit test.
        self.service._build_ingestion_service = (
            lambda user_id: FakeIngestionService()
        )

        result = self.service.search(
            user_id="user-1",
            query="marketing",
        )

        self.assertEqual(
            result,
            [],
        )

    def test_ingestion_result_shape(self):
        fake_ingestion = (
            FakeIngestionService()
        )

        self.service._build_ingestion_service = (
            lambda user_id: fake_ingestion
        )

        file_path = (
            Path(self.temp_dir)
            / "brand.txt"
        )

        file_path.write_text(
            "Our brand focuses on digital marketing.",
            encoding="utf-8",
        )

        result = self.service.ingest_document(
            user_id="user-1",
            file_path=file_path,
            filename="brand.txt",
        )

        self.assertEqual(
            result["status"],
            "INDEXED",
        )

        self.assertEqual(
            result["extension"],
            ".txt",
        )

        self.assertGreater(
            result["chunks_created"],
            0,
        )

    def test_ingestion_and_search_flow(self):
        fake_ingestion = (
            FakeIngestionService()
        )

        self.service._build_ingestion_service = (
            lambda user_id: fake_ingestion
        )

        file_path = (
            Path(self.temp_dir)
            / "brand.txt"
        )

        file_path.write_text(
            (
                "MarketingOS is a digital marketing "
                "platform for small businesses."
            ),
            encoding="utf-8",
        )

        self.service.ingest_document(
            user_id="user-1",
            file_path=file_path,
            filename="brand.txt",
        )

        result = fake_ingestion.search(
            query="digital marketing",
            top_k=3,
        )

        self.assertEqual(
            len(result),
            1,
        )

        self.assertIn(
            "digital marketing",
            result[0]["text"],
        )


if __name__ == "__main__":
    unittest.main()