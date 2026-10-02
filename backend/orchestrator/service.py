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

    The planner decides which agents should be used.

    The orchestrator is responsible for:
    - dependency resolution
    - task ordering
    - parallel execution of independent tasks
    - output propagation
    - input propagation
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

        # Preserve the existing Shared Context architecture.
        shared_context = dict(context or {})

        executions = {
            task.id: TaskExecution(task=task)
            for task in plan.tasks
        }

        # Stores outputs by task ID.
        #
        # IMPORTANT:
        # This stores the COMPLETE agent result wrapper.
        #
        # Example:
        # {
        #     "agent": "research",
        #     "status": "COMPLETED",
        #     "summary": "...",
        #     "data": {
        #         "topic": "...",
        #         ...
        #     }
        # }
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

                # -------------------------------------------------
                # Find tasks whose dependencies are resolved
                # -------------------------------------------------

                for execution in pending_tasks:

                    task = execution.task

                    dependency_states = [
                        executions[dependency].status
                        for dependency in task.depends_on
                    ]

                    # Dependency still running/pending.
                    if any(
                        state in {
                            TaskStatus.PENDING,
                            TaskStatus.RUNNING,
                        }
                        for state in dependency_states
                    ):
                        continue

                    # Dependency failed/blocked.
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

                # -------------------------------------------------
                # No executable tasks
                # -------------------------------------------------

                if not ready_tasks:

                    if progress_made:
                        continue

                    raise OrchestrationError(
                        "Orchestration could not make progress. "
                        "The execution plan may contain an unresolved "
                        "dependency."
                    )

                futures = {}

                # -------------------------------------------------
                # Start all ready tasks
                # -------------------------------------------------

                for execution in ready_tasks:

                    agent_name = execution.task.agent.value

                    handler = self.agent_handlers.get(
                        agent_name
                    )

                    if handler is None:

                        execution.status = TaskStatus.FAILED
                        execution.error = (
                            f"No handler registered for agent "
                            f"'{agent_name}'."
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
                        plan=plan,
                    )

                    future = executor.submit(
                        self._call_handler,
                        handler,
                        execution.task,
                        task_inputs,
                        shared_context,
                    )

                    futures[future] = execution

                # -------------------------------------------------
                # Collect completed tasks
                # -------------------------------------------------

                for future in as_completed(futures):

                    execution = futures[future]

                    try:

                        execution.result = future.result()

                        # IMPORTANT:
                        # An agent can return a structured FAILED result
                        # without throwing a Python exception.
                        #
                        # Example:
                        #
                        # {
                        #     "status": "FAILED",
                        #     "error": "..."
                        # }
                        #
                        # Treat that as an actual task failure.
                        result_status = None

                        if isinstance(execution.result, dict):
                            result_status = execution.result.get(
                                "status"
                            )

                        if result_status == "FAILED":
                            execution.status = TaskStatus.FAILED
                            execution.error = (
                                execution.result.get("error")
                                or "Agent execution failed."
                            )

                        else:
                            execution.status = TaskStatus.COMPLETED

                            # Store complete output by task ID.
                            #
                            # Example:
                            # outputs["research_1"] = {
                            #     "agent": "research",
                            #     "status": "COMPLETED",
                            #     "data": {...}
                            # }
                            outputs[
                                execution.task.id
                            ] = execution.result

                            # Store complete result using agent name.
                            #
                            # Example:
                            # shared_context["research"] = {
                            #     "agent": "research",
                            #     "status": "COMPLETED",
                            #     "data": {...}
                            # }
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

    # =============================================================
    # HANDLER EXECUTION
    # =============================================================

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

    # =============================================================
    # TASK INPUT BUILDING
    # =============================================================

    @staticmethod
    def _build_task_inputs(
        task: PlannerTask,
        outputs: dict[str, Any],
        shared_context: dict[str, Any],
        plan: ExecutionPlan,
    ) -> dict[str, Any]:
        """
        Build the input package for a task.

        Inputs can come from:

        1. Dependency outputs
        2. Explicit shared context
        3. Original user request

        Dependency outputs are exposed using both:

        - dependency task ID
        - dependency agent name

        Example:

            research_1
                ->
            inputs["research"]

        and:

            competitor_1
                ->
            inputs["competitor"]

        IMPORTANT:
        AgentAdapter returns a complete AgentResult wrapper:

        {
            "agent": "research",
            "status": "COMPLETED",
            "summary": "...",
            "data": {
                "topic": "...",
                ...
            },
            "error": None,
            "confidence": 0.8
        }

        Downstream agents should receive only the actual
        business data under "data", not the complete wrapper.

        Therefore dependency outputs are unwrapped before
        being passed to downstream agents.
        """

        inputs: dict[str, Any] = {}

        # ---------------------------------------------------------
        # 1. Dependency outputs
        # ---------------------------------------------------------

        for dependency_id in task.depends_on:

            if dependency_id not in outputs:
                continue

            dependency_output = outputs[
                dependency_id
            ]

            # -----------------------------------------------------
            # IMPORTANT:
            #
            # AgentAdapter returns:
            #
            # {
            #     "agent": "research",
            #     "status": "COMPLETED",
            #     "summary": "...",
            #     "data": {
            #         "topic": "...",
            #         ...
            #     }
            # }
            #
            # Downstream agents such as Competitor, SEO and
            # Content expect:
            #
            # {
            #     "topic": "...",
            #     ...
            # }
            #
            # So unwrap the "data" field here.
            # -----------------------------------------------------

            if (
                isinstance(dependency_output, dict)
                and dependency_output.get("data") is not None
            ):
                dependency_input = dependency_output["data"]

            else:
                dependency_input = dependency_output

            # -----------------------------------------------------
            # Keep task-id keyed output.
            #
            # Useful for tracing/debugging.
            #
            # Example:
            #
            # inputs["research_1"] = {
            #     "topic": "...",
            #     ...
            # }
            # -----------------------------------------------------

            inputs[dependency_id] = dependency_input

            # -----------------------------------------------------
            # Resolve the dependency's actual agent name.
            # -----------------------------------------------------

            dependency_task = next(
                (
                    planner_task
                    for planner_task in plan.tasks
                    if planner_task.id == dependency_id
                ),
                None,
            )

            if dependency_task is not None:

                dependency_agent_name = (
                    dependency_task.agent.value
                )

                # -------------------------------------------------
                # Example:
                #
                # research_1 -> research
                # competitor_1 -> competitor
                # seo_1 -> seo
                #
                # Downstream agents can now directly access:
                #
                # inputs["research"]
                # inputs["competitor"]
                # inputs["seo"]
                # -------------------------------------------------

                inputs[
                    dependency_agent_name
                ] = dependency_input

        # ---------------------------------------------------------
        # 2. Explicit shared-context inputs
        # ---------------------------------------------------------

        for required_input in task.required_inputs:

            if required_input in shared_context:

                shared_value = shared_context[
                    required_input
                ]

                # Shared context can also contain a complete
                # AgentResult wrapper. If it does, unwrap it
                # before passing it to the agent.
                if (
                    isinstance(shared_value, dict)
                    and shared_value.get("data") is not None
                ):
                    inputs[required_input] = (
                        shared_value["data"]
                    )
                else:
                    inputs[required_input] = shared_value

        # ---------------------------------------------------------
        # 3. Map original user request
        # ---------------------------------------------------------

        user_request = shared_context.get(
            "user_request"
        )

        if isinstance(user_request, str):
            user_request = user_request.strip()

        if user_request:

            # Research Agent
            if (
                "topic" in task.required_inputs
                and "topic" not in inputs
            ):
                inputs["topic"] = user_request

            # Image / Content Agent
            if (
                "prompt" in task.required_inputs
                and "prompt" not in inputs
            ):
                inputs["prompt"] = user_request

            # Generic query-based agents
            if (
                "query" in task.required_inputs
                and "query" not in inputs
            ):
                inputs["query"] = user_request

            # Generic input fallback
            if (
                "input" in task.required_inputs
                and "input" not in inputs
            ):
                inputs["input"] = user_request

        return inputs

    # =============================================================
    # FINAL RESULT
    # =============================================================

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

        # Return the actual failed result when available.
        #
        # This makes debugging much easier because the caller
        # can see the agent's error instead of receiving None.
        if final_execution.result is not None:
            return final_execution.result

        return None

    # =============================================================
    # OVERALL STATUS
    # =============================================================

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