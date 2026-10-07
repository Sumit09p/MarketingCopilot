"""Persistence service for agent execution runs."""

from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import (
    ConfigurationError,
    ConnectionFailure,
    ServerSelectionTimeoutError,
)

from backend.database import (
    DatabaseConnectionError,
    DatabaseNotConfiguredError,
    get_database,
)

from backend.models.agent_run import (
    AGENT_RUNS_COLLECTION,
    agent_run_document_to_response,
    build_agent_run_document,
)


class AgentRunService:
    """
    Persist agent execution lifecycle in MongoDB.

    Persistence is best-effort.

    If MongoDB is unavailable, agent execution should continue
    normally without crashing the marketing pipeline.
    """

    def __init__(
        self,
        database: Any | None = None,
    ) -> None:
        self._database = database
        self._collection = None

    # =============================================================
    # DATABASE / COLLECTION
    # =============================================================

    @property
    def collection(self):
        """Return the agent_runs collection."""

        if self._collection is None:

            database = (
                self._database
                if self._database is not None
                else get_database()
            )

            self._collection = database[
                AGENT_RUNS_COLLECTION
            ]

        return self._collection

    # =============================================================
    # ID HELPER
    # =============================================================

    @staticmethod
    def _build_id_filter(
        run_id: str | ObjectId,
    ) -> dict[str, Any]:
        """
        Build a MongoDB _id filter.

        Production MongoDB records normally use ObjectId.

        Tests may use simple string IDs, so both are supported.
        """

        if isinstance(run_id, ObjectId):
            return {
                "_id": run_id
            }

        if not isinstance(run_id, str):
            return {
                "_id": run_id
            }

        try:
            return {
                "_id": ObjectId(run_id)
            }

        except (
            InvalidId,
            TypeError,
        ):
            return {
                "_id": run_id
            }

    # =============================================================
    # START RUN
    # =============================================================

    def start_run(
        self,
        *,
        user_id: str | None,
        conversation_id: str | None,
        task_id: str,
        agent: str,
        input_data: dict[str, Any] | None,
        attempt: int,
    ) -> str | None:
        """
        Create a RUNNING agent execution record.
        """

        now = datetime.now(UTC)

        document = build_agent_run_document(
            user_id=user_id,
            conversation_id=conversation_id,
            task_id=task_id,
            agent=agent,
            input_data=input_data,
            status="RUNNING",
            attempt=attempt,
            created_at=now,
            started_at=now,
            completed_at=None,
            result=None,
            confidence=None,
            error=None,
        )

        try:
            result = self.collection.insert_one(
                document
            )

            return str(
                result.inserted_id
            )

        except (
            DatabaseNotConfiguredError,
            DatabaseConnectionError,
            ConnectionFailure,
            ServerSelectionTimeoutError,
            ConfigurationError,
        ):
            return None

    # =============================================================
    # COMPLETE RUN
    # =============================================================

    def complete_run(
        self,
        *,
        run_id: str | ObjectId | None,
        result: Any,
        confidence: float | None = None,
    ) -> bool:
        """
        Mark an agent execution as COMPLETED.
        """

        if run_id is None:
            return False

        query = self._build_id_filter(
            run_id
        )

        try:
            update_result = self.collection.update_one(
                query,
                {
                    "$set": {
                        "status": "COMPLETED",
                        "completed_at": datetime.now(UTC),
                        "result": result,
                        "confidence": confidence,
                        "error": None,
                    }
                },
            )

            return (
                update_result.modified_count > 0
            )

        except (
            DatabaseNotConfiguredError,
            DatabaseConnectionError,
            ConnectionFailure,
            ServerSelectionTimeoutError,
            ConfigurationError,
        ):
            return False

    # =============================================================
    # FAIL RUN
    # =============================================================

    def fail_run(
        self,
        *,
        run_id: str | ObjectId | None,
        error: str,
        result: Any = None,
    ) -> bool:
        """
        Mark an agent execution as FAILED.
        """

        if run_id is None:
            return False

        query = self._build_id_filter(
            run_id
        )

        try:
            update_result = self.collection.update_one(
                query,
                {
                    "$set": {
                        "status": "FAILED",
                        "completed_at": datetime.now(UTC),
                        "result": result,
                        "error": error,
                    }
                },
            )

            return (
                update_result.modified_count > 0
            )

        except (
            DatabaseNotConfiguredError,
            DatabaseConnectionError,
            ConnectionFailure,
            ServerSelectionTimeoutError,
            ConfigurationError,
        ):
            return False

    # =============================================================
    # BLOCK RUN
    # =============================================================

    def block_run(
        self,
        *,
        user_id: str | None,
        conversation_id: str | None,
        task_id: str,
        agent: str,
        input_data: dict[str, Any] | None = None,
        attempt: int = 0,
        error: str,
    ) -> str | None:
        """
        Create a BLOCKED agent execution record.

        A blocked task never actually executed.

        Therefore:

            status       = BLOCKED
            started_at   = None
            completed_at = current time
        """

        now = datetime.now(UTC)

        document = build_agent_run_document(
            user_id=user_id,
            conversation_id=conversation_id,
            task_id=task_id,
            agent=agent,
            input_data=input_data,
            status="BLOCKED",
            attempt=attempt,
            created_at=now,
            started_at=None,
            completed_at=now,
            result=None,
            confidence=None,
            error=error,
        )

        try:
            result = self.collection.insert_one(
                document
            )

            return str(
                result.inserted_id
            )

        except (
            DatabaseNotConfiguredError,
            DatabaseConnectionError,
            ConnectionFailure,
            ServerSelectionTimeoutError,
            ConfigurationError,
        ):
            return None

    # =============================================================
    # GET SINGLE RUN
    # =============================================================

    def get_run(
        self,
        run_id: str | ObjectId | None,
    ) -> dict[str, Any] | None:
        """
        Retrieve a single agent execution record.
        """

        if run_id is None:
            return None

        query = self._build_id_filter(
            run_id
        )

        try:
            document = self.collection.find_one(
                query
            )

            if document is None:
                return None

            return agent_run_document_to_response(
                document
            )

        except (
            DatabaseNotConfiguredError,
            DatabaseConnectionError,
            ConnectionFailure,
            ServerSelectionTimeoutError,
            ConfigurationError,
        ):
            return None

    # =============================================================
    # GET CONVERSATION RUNS
    # =============================================================

    def get_conversation_runs(
        self,
        *,
        conversation_id: str,
        user_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieve all agent runs for a conversation.

        Results are returned in execution/creation order:

            research
            competitor
            seo
            content
            image
        """

        query: dict[str, Any] = {
            "conversation_id": conversation_id
        }

        if user_id is not None:
            query["user_id"] = user_id

        try:
            cursor = self.collection.find(
                query
            ).sort(
                "created_at",
                1,
            )

            return [
                agent_run_document_to_response(
                    document
                )
                for document in cursor
            ]

        except (
            DatabaseNotConfiguredError,
            DatabaseConnectionError,
            ConnectionFailure,
            ServerSelectionTimeoutError,
            ConfigurationError,
        ):
            return []

