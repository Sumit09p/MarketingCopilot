"""Tests for agent execution persistence."""

import unittest
from datetime import UTC, datetime


class FakeInsertResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class FakeUpdateResult:
    def __init__(self, modified_count):
        self.modified_count = modified_count


class FakeCollection:
    def __init__(self):
        self.documents = []

    def insert_one(self, document):
        document = dict(document)

        document["_id"] = (
            f"fake-id-{len(self.documents) + 1}"
        )

        self.documents.append(document)

        return FakeInsertResult(
            document["_id"]
        )

    def update_one(self, query, update):
        for document in self.documents:

            if document["_id"] == query["_id"]:

                values = update.get(
                    "$set",
                    {},
                )

                document.update(values)

                return FakeUpdateResult(1)

        return FakeUpdateResult(0)

    def find_one(self, query):

        for document in self.documents:

            if document["_id"] == query["_id"]:
                return document

        return None

    def find(self, query):
        matches = []

        for document in self.documents:

            matches_query = True

            for key, value in query.items():

                if document.get(key) != value:
                    matches_query = False
                    break

            if matches_query:
                matches.append(document)

        class FakeCursor:
            def __init__(self, documents):
                self.documents = documents

            def sort(self, key, direction):
                reverse = direction < 0

                self.documents.sort(
                    key=lambda item: item.get(key),
                    reverse=reverse,
                )

                return self

            def __iter__(self):
                return iter(self.documents)

        return FakeCursor(matches)


class FakeDatabase:
    def __init__(self):
        self.collections = {}

    def __getitem__(self, name):
        if name not in self.collections:
            self.collections[name] = (
                FakeCollection()
            )

        return self.collections[name]


from services.agent_run_service import (
    AgentRunService,
)


class TestAgentRunService(unittest.TestCase):

    def setUp(self):
        self.database = FakeDatabase()

        self.service = AgentRunService(
            database=self.database
        )

    def test_start_run_creates_running_record(self):
        run_id = self.service.start_run(
            user_id="user-1",
            conversation_id="conversation-1",
            task_id="research_1",
            agent="research",
            input_data={
                "topic": "fitness"
            },
            attempt=1,
        )

        self.assertIsNotNone(
            run_id
        )

        document = (
            self.database[
                "agent_runs"
            ].documents[0]
        )

        self.assertEqual(
            document["user_id"],
            "user-1",
        )

        self.assertEqual(
            document["conversation_id"],
            "conversation-1",
        )

        self.assertEqual(
            document["task_id"],
            "research_1",
        )

        self.assertEqual(
            document["agent"],
            "research",
        )

        self.assertEqual(
            document["status"],
            "RUNNING",
        )

        self.assertEqual(
            document["attempt"],
            1,
        )

        self.assertEqual(
            document["input"],
            {
                "topic": "fitness"
            },
        )

        self.assertIsNotNone(
            document["started_at"]
        )

    def test_complete_run_updates_status(self):
        run_id = self.service.start_run(
            user_id="user-1",
            conversation_id="conversation-1",
            task_id="research_1",
            agent="research",
            input_data={
                "topic": "fitness"
            },
            attempt=1,
        )

        updated = (
            self.service.complete_run(
                run_id=run_id,
                result={
                    "topic": "fitness",
                    "summary": "Market research",
                },
                confidence=0.9,
            )
        )

        self.assertTrue(updated)

        document = (
            self.database[
                "agent_runs"
            ].documents[0]
        )

        self.assertEqual(
            document["status"],
            "COMPLETED",
        )

        self.assertEqual(
            document["result"],
            {
                "topic": "fitness",
                "summary": "Market research",
            },
        )

        self.assertEqual(
            document["confidence"],
            0.9,
        )

        self.assertIsNotNone(
            document["completed_at"]
        )

        self.assertIsNone(
            document["error"]
        )

    def test_fail_run_updates_status(self):
        run_id = self.service.start_run(
            user_id="user-1",
            conversation_id="conversation-1",
            task_id="research_1",
            agent="research",
            input_data={
                "topic": "fitness"
            },
            attempt=1,
        )

        updated = self.service.fail_run(
            run_id=run_id,
            error="Research provider failed.",
        )

        self.assertTrue(updated)

        document = (
            self.database[
                "agent_runs"
            ].documents[0]
        )

        self.assertEqual(
            document["status"],
            "FAILED",
        )

        self.assertEqual(
            document["error"],
            "Research provider failed.",
        )

        self.assertIsNotNone(
            document["completed_at"]
        )

    def test_block_run_creates_blocked_record(self):
        run_id = self.service.block_run(
            user_id="user-1",
            conversation_id="conversation-1",
            task_id="content_1",
            agent="content",
            input_data={
                "research": {
                    "topic": "fitness"
                }
            },
            attempt=0,
            error="Research task failed.",
        )

        self.assertIsNotNone(
            run_id
        )

        document = (
            self.database[
                "agent_runs"
            ].documents[0]
        )

        self.assertEqual(
            document["status"],
            "BLOCKED",
        )

        self.assertEqual(
            document["error"],
            "Research task failed.",
        )

        self.assertIsNone(
            document["started_at"]
        )

        self.assertIsNotNone(
            document["completed_at"]
        )

    def test_get_run_returns_saved_record(self):
        run_id = self.service.start_run(
            user_id="user-1",
            conversation_id="conversation-1",
            task_id="research_1",
            agent="research",
            input_data={
                "topic": "fitness"
            },
            attempt=1,
        )

        result = self.service.get_run(
            run_id
        )

        self.assertIsNotNone(
            result
        )

        self.assertEqual(
            result["id"],
            run_id,
        )

        self.assertEqual(
            result["agent"],
            "research",
        )

        self.assertEqual(
            result["status"],
            "RUNNING",
        )

    def test_get_conversation_runs(self):
        self.service.start_run(
            user_id="user-1",
            conversation_id="conversation-1",
            task_id="research_1",
            agent="research",
            input_data={
                "topic": "fitness"
            },
            attempt=1,
        )

        self.service.start_run(
            user_id="user-1",
            conversation_id="conversation-1",
            task_id="seo_1",
            agent="seo",
            input_data={
                "query": "fitness SEO"
            },
            attempt=1,
        )

        self.service.start_run(
            user_id="user-2",
            conversation_id="conversation-2",
            task_id="research_1",
            agent="research",
            input_data={
                "topic": "finance"
            },
            attempt=1,
        )

        results = (
            self.service.get_conversation_runs(
                conversation_id="conversation-1",
                user_id="user-1",
            )
        )

        self.assertEqual(
            len(results),
            2,
        )

        self.assertEqual(
            results[0]["agent"],
            "research",
        )

        self.assertEqual(
            results[1]["agent"],
            "seo",
        )


if __name__ == "__main__":
    unittest.main()