"""Dependency-aware execution orchestrator."""

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from orchestrator.schemas import (
    OrchestrationResult,
    TaskExecution,
    TaskStatus,
)
from planner.schemas import ExecutionPlan, PlannerTask


class OrchestrationError(Exception):
    """Raised when orchestration cannot be completed."""


class OrchestratorService:
    """
    Execute planner tasks according to their dependencies.

    The orchestrator does not decide which agents should be used.
    The planner already made that decision.

    The orchestrator is responsible for:
    - dependency resolution
    - task ordering
    - parallel execution of independent tasks
    - output propagation
    - failure handling
    - blocked-task handling
    """

    def __init__(
        self,
        agent_handlers: dict[str, Callable[..., Any]] | None = None,
        max_workers: int = 4,
    ) -> None:
        """Initialize the orchestrator."""

        if max_workers < 1:
            raise ValueError(
                "max_workers must be at least 1."
            )

        self.agent_handlers = agent_handlers or {}
        self.max_workers = max_workers

    def execute(
        self,
        plan: ExecutionPlan,
        context: dict[str, Any] | None = None,
    ) -> OrchestrationResult:
        """
        Execute all tasks according to their dependencies.

        Independent ready tasks execute concurrently.
        """

        shared_context = dict(context or {})

        executions = {
            task.id: TaskExecution(task=task)
            for task in plan.tasks
        }

        outputs: dict[str, Any] = {}

        with ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:

            while True:
                pending_tasks = [
                    execution
                    for execution in executions.values()
                    if execution.status == TaskStatus.PENDING
                ]

                if not pending_tasks:
                    break

                progress_made = False
                ready_tasks: list[TaskExecution] = []

                for execution in pending_tasks:
                    task = execution.task

                    dependency_states = [
                        executions[dependency].status
                        for dependency in task.depends_on
                    ]

                    if any(
                        state in {
                            TaskStatus.PENDING,
                            TaskStatus.RUNNING,
                        }
                        for state in dependency_states
                    ):
                        continue

                    if any(
                        state in {
                            TaskStatus.FAILED,
                            TaskStatus.BLOCKED,
                        }
                        for state in dependency_states
                    ):
                        execution.status = TaskStatus.BLOCKED
                        execution.error = (
                            "Task blocked because one or more "
                            "dependencies failed or were blocked."
                        )
                        progress_made = True
                        continue

                    ready_tasks.append(execution)

                if not ready_tasks:
                    if progress_made:
                        continue

                    raise OrchestrationError(
                        "Orchestration could not make progress. "
                        "The execution plan may contain an unresolved "
                        "dependency."
                    )

                futures = {}

                for execution in ready_tasks:
                    handler = self.agent_handlers.get(
                        execution.task.agent.value
                    )

                    if handler is None:
                        execution.status = TaskStatus.FAILED
                        execution.error = (
                            f"No handler registered for agent "
                            f"'{execution.task.agent.value}'."
                        )
                        execution.attempts += 1
                        progress_made = True
                        continue

                    execution.status = TaskStatus.RUNNING
                    execution.attempts += 1

                    task_inputs = self._build_task_inputs(
                        task=execution.task,
                        outputs=outputs,
                        shared_context=shared_context,
                    )

                    future = executor.submit(
                        self._call_handler,
                        handler,
                        execution.task,
                        task_inputs,
                        shared_context,
                    )

                    futures[future] = execution

                for future in as_completed(futures):
                    execution = futures[future]

                    try:
                        execution.result = future.result()
                        execution.status = TaskStatus.COMPLETED

                        outputs[
                            execution.task.id
                        ] = execution.result

                        shared_context[
                            execution.task.agent.value
                        ] = execution.result

                    except Exception as exc:
                        execution.status = TaskStatus.FAILED
                        execution.error = str(exc)

                    progress_made = True

                if not progress_made:
                    raise OrchestrationError(
                        "Orchestration could not make progress."
                    )

        final_result = self._build_final_result(
            plan=plan,
            executions=executions,
        )

        overall_status = self._get_overall_status(
            executions
        )

        return OrchestrationResult(
            status=overall_status,
            tasks=list(executions.values()),
            final_result=final_result,
        )

    @staticmethod
    def _call_handler(
        handler: Callable[..., Any],
        task: PlannerTask,
        task_inputs: dict[str, Any],
        shared_context: dict[str, Any],
    ) -> Any:
        """Execute an agent handler."""

        return handler(
            task=task,
            inputs=task_inputs,
            context=shared_context,
        )

    @staticmethod
    def _build_task_inputs(
        task: PlannerTask,
        outputs: dict[str, Any],
        shared_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Build the input package for a task."""

        inputs: dict[str, Any] = {}

        for dependency_id in task.depends_on:
            if dependency_id in outputs:
                inputs[dependency_id] = outputs[
                    dependency_id
                ]

        for required_input in task.required_inputs:
            if required_input in shared_context:
                inputs[required_input] = shared_context[
                    required_input
                ]

        return inputs

    @staticmethod
    def _build_final_result(
        plan: ExecutionPlan,
        executions: dict[str, TaskExecution],
    ) -> Any:
        """Return the result of the final task in the plan."""

        if not plan.tasks:
            return None

        final_task = plan.tasks[-1]

        final_execution = executions[
            final_task.id
        ]

        if final_execution.status == TaskStatus.COMPLETED:
            return final_execution.result

        return None

    @staticmethod
    def _get_overall_status(
        executions: dict[str, TaskExecution],
    ) -> str:
        """Determine the overall orchestration status."""

        states = {
            execution.status
            for execution in executions.values()
        }

        if TaskStatus.FAILED in states:
            return "FAILED"

        if TaskStatus.BLOCKED in states:
            return "BLOCKED"

        if states == {TaskStatus.COMPLETED}:
            return "COMPLETED"

        return "INCOMPLETE"