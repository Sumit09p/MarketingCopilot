"""Tests for dependency-aware orchestrator execution."""

import time
import unittest

from guardrails.schemas import AgentType
from orchestrator.schemas import TaskStatus
from orchestrator.service import OrchestratorService
from planner.schemas import ExecutionPlan, PlannerTask


class TestOrchestratorService(unittest.TestCase):
    """Test OrchestratorService behavior."""

    def test_independent_tasks_execute_in_parallel(self) -> None:
        start_times = {}

        def research_handler(task, inputs, context):
            start_times["research"] = time.perf_counter()
            time.sleep(0.5)
            return "research"

        def analytics_handler(task, inputs, context):
            start_times["analytics"] = time.perf_counter()
            time.sleep(0.5)
            return "analytics"

        orchestrator = OrchestratorService(
            agent_handlers={
                "research": research_handler,
                "analytics": analytics_handler,
            },
            max_workers=2,
        )

        plan = ExecutionPlan(
            goal="Run independent tasks in parallel.",
            tasks=[
                PlannerTask(
                    id="research_1",
                    agent=AgentType.RESEARCH,
                ),
                PlannerTask(
                    id="analytics_1",
                    agent=AgentType.ANALYTICS,
                ),
            ],
        )

        started_at = time.perf_counter()

        result = orchestrator.execute(plan)

        elapsed = time.perf_counter() - started_at

        self.assertEqual(
            result.status,
            "COMPLETED",
        )

        self.assertEqual(
            result.tasks[0].status,
            TaskStatus.COMPLETED,
        )

        self.assertEqual(
            result.tasks[1].status,
            TaskStatus.COMPLETED,
        )

        self.assertIn(
            "research",
            start_times,
        )

        self.assertIn(
            "analytics",
            start_times,
        )

        # Sequential execution would take approximately 1 second.
        # Parallel execution should finish substantially faster.
        self.assertLess(
            elapsed,
            0.9,
        )

        # Both tasks should start very close to each other.
        self.assertLess(
            abs(
                start_times["research"]
                - start_times["analytics"]
            ),
            0.2,
        )

    def test_single_task_executes_successfully(self) -> None:
        def research_handler(task, inputs, context):
            return "research result"

        orchestrator = OrchestratorService(
            agent_handlers={
                "research": research_handler,
            }
        )

        plan = ExecutionPlan(
            goal="Research the fitness market.",
            tasks=[
                PlannerTask(
                    id="research_1",
                    agent=AgentType.RESEARCH,
                )
            ],
        )

        result = orchestrator.execute(plan)

        self.assertEqual(
            result.status,
            "COMPLETED",
        )

        self.assertEqual(
            result.tasks[0].status,
            TaskStatus.COMPLETED,
        )

        self.assertEqual(
            result.tasks[0].result,
            "research result",
        )

        self.assertEqual(
            result.final_result,
            "research result",
        )

    def test_task_receives_context(self) -> None:
        received = {}

        def research_handler(task, inputs, context):
            received.update(context)
            return "done"

        orchestrator = OrchestratorService(
            agent_handlers={
                "research": research_handler,
            }
        )

        plan = ExecutionPlan(
            goal="Research the market.",
            tasks=[
                PlannerTask(
                    id="research_1",
                    agent=AgentType.RESEARCH,
                )
            ],
        )

        orchestrator.execute(
            plan,
            context={
                "brand": "Test Brand",
                "industry": "Fitness",
            },
        )

        self.assertEqual(
            received["brand"],
            "Test Brand",
        )

        self.assertEqual(
            received["industry"],
            "Fitness",
        )

    def test_dependency_order_is_respected(self) -> None:
        execution_order = []

        def research_handler(task, inputs, context):
            execution_order.append("research")
            return "research output"

        def competitor_handler(task, inputs, context):
            execution_order.append("competitor")
            return "competitor output"

        def content_handler(task, inputs, context):
            execution_order.append("content")
            return "content output"

        orchestrator = OrchestratorService(
            agent_handlers={
                "research": research_handler,
                "competitor": competitor_handler,
                "content": content_handler,
            }
        )

        plan = ExecutionPlan(
            goal="Create marketing content.",
            tasks=[
                PlannerTask(
                    id="research_1",
                    agent=AgentType.RESEARCH,
                ),
                PlannerTask(
                    id="competitor_1",
                    agent=AgentType.COMPETITOR,
                    depends_on=["research_1"],
                    required_inputs=["research"],
                ),
                PlannerTask(
                    id="content_1",
                    agent=AgentType.CONTENT,
                    depends_on=[
                        "research_1",
                        "competitor_1",
                    ],
                    required_inputs=[
                        "research",
                        "competitor",
                    ],
                ),
            ],
        )

        result = orchestrator.execute(plan)

        self.assertEqual(
            execution_order,
            [
                "research",
                "competitor",
                "content",
            ],
        )

        self.assertEqual(
            result.status,
            "COMPLETED",
        )

    def test_dependency_output_is_passed_to_next_task(self) -> None:
        received_inputs = {}

        def research_handler(task, inputs, context):
            return {
                "topic": "fitness",
                "audience": "young adults",
            }

        def competitor_handler(task, inputs, context):
            received_inputs.update(inputs)
            return "competitor analysis"

        orchestrator = OrchestratorService(
            agent_handlers={
                "research": research_handler,
                "competitor": competitor_handler,
            }
        )

        plan = ExecutionPlan(
            goal="Research competitors.",
            tasks=[
                PlannerTask(
                    id="research_1",
                    agent=AgentType.RESEARCH,
                ),
                PlannerTask(
                    id="competitor_1",
                    agent=AgentType.COMPETITOR,
                    depends_on=["research_1"],
                    required_inputs=["research"],
                ),
            ],
        )

        orchestrator.execute(plan)

        self.assertEqual(
            received_inputs["research_1"],
            {
                "topic": "fitness",
                "audience": "young adults",
            },
        )

        self.assertEqual(
            received_inputs["research"],
            {
                "topic": "fitness",
                "audience": "young adults",
            },
        )

    def test_failed_task_is_marked_failed(self) -> None:
        def research_handler(task, inputs, context):
            raise RuntimeError("Research service failed.")

        orchestrator = OrchestratorService(
            agent_handlers={
                "research": research_handler,
            }
        )

        plan = ExecutionPlan(
            goal="Research the market.",
            tasks=[
                PlannerTask(
                    id="research_1",
                    agent=AgentType.RESEARCH,
                )
            ],
        )

        result = orchestrator.execute(plan)

        self.assertEqual(
            result.status,
            "FAILED",
        )

        self.assertEqual(
            result.tasks[0].status,
            TaskStatus.FAILED,
        )

        self.assertEqual(
            result.tasks[0].error,
            "Research service failed.",
        )

        self.assertEqual(
            result.tasks[0].attempts,
            1,
        )

    def test_missing_agent_handler_fails_task(self) -> None:
        orchestrator = OrchestratorService()

        plan = ExecutionPlan(
            goal="Run research.",
            tasks=[
                PlannerTask(
                    id="research_1",
                    agent=AgentType.RESEARCH,
                )
            ],
        )

        result = orchestrator.execute(plan)

        self.assertEqual(
            result.status,
            "FAILED",
        )

        self.assertEqual(
            result.tasks[0].status,
            TaskStatus.FAILED,
        )

        self.assertIn(
            "No handler registered",
            result.tasks[0].error,
        )

    def test_dependent_task_is_blocked_after_failure(self) -> None:
        def research_handler(task, inputs, context):
            raise RuntimeError("Research failed.")

        def content_handler(task, inputs, context):
            return "content should not execute"

        orchestrator = OrchestratorService(
            agent_handlers={
                "research": research_handler,
                "content": content_handler,
            }
        )

        plan = ExecutionPlan(
            goal="Create content using research.",
            tasks=[
                PlannerTask(
                    id="research_1",
                    agent=AgentType.RESEARCH,
                ),
                PlannerTask(
                    id="content_1",
                    agent=AgentType.CONTENT,
                    depends_on=["research_1"],
                ),
            ],
        )

        result = orchestrator.execute(plan)

        self.assertEqual(
            result.tasks[0].status,
            TaskStatus.FAILED,
        )

        self.assertEqual(
            result.tasks[1].status,
            TaskStatus.BLOCKED,
        )

        self.assertEqual(
            result.status,
            "FAILED",
        )

    def test_independent_tasks_can_both_execute(self) -> None:
        executed = []

        def research_handler(task, inputs, context):
            executed.append("research")
            return "research"

        def analytics_handler(task, inputs, context):
            executed.append("analytics")
            return "analytics"

        orchestrator = OrchestratorService(
            agent_handlers={
                "research": research_handler,
                "analytics": analytics_handler,
            }
        )

        plan = ExecutionPlan(
            goal="Run independent tasks.",
            tasks=[
                PlannerTask(
                    id="research_1",
                    agent=AgentType.RESEARCH,
                ),
                PlannerTask(
                    id="analytics_1",
                    agent=AgentType.ANALYTICS,
                ),
            ],
        )

        result = orchestrator.execute(plan)

        self.assertEqual(
            result.status,
            "COMPLETED",
        )

        self.assertEqual(
            set(executed),
            {
                "research",
                "analytics",
            },
        )

    def test_attempt_count_is_incremented(self) -> None:
        def research_handler(task, inputs, context):
            return "success"

        orchestrator = OrchestratorService(
            agent_handlers={
                "research": research_handler,
            }
        )

        plan = ExecutionPlan(
            goal="Test attempts.",
            tasks=[
                PlannerTask(
                    id="research_1",
                    agent=AgentType.RESEARCH,
                )
            ],
        )

        result = orchestrator.execute(plan)

        self.assertEqual(
            result.tasks[0].attempts,
            1,
        )

    def test_final_result_is_last_task_result(self) -> None:
        def research_handler(task, inputs, context):
            return "research"

        def content_handler(task, inputs, context):
            return "final content"

        orchestrator = OrchestratorService(
            agent_handlers={
                "research": research_handler,
                "content": content_handler,
            }
        )

        plan = ExecutionPlan(
            goal="Create final content.",
            tasks=[
                PlannerTask(
                    id="research_1",
                    agent=AgentType.RESEARCH,
                ),
                PlannerTask(
                    id="content_1",
                    agent=AgentType.CONTENT,
                    depends_on=["research_1"],
                ),
            ],
        )

        result = orchestrator.execute(plan)

        self.assertEqual(
            result.final_result,
            "final content",
        )


if __name__ == "__main__":
    unittest.main()