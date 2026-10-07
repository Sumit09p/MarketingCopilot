"""Dependency-aware execution orchestrator."""

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from backend.orchestrator.schemas import (
    OrchestrationResult,
    TaskExecution,
    TaskStatus,
)
from backend.planner.schemas import ExecutionPlan, PlannerTask


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
    - agent execution persistence
    """

    def __init__(
        self,
        agent_handlers: dict[str, Callable[..., Any]] | None = None,
        max_workers: int = 4,
        agent_run_service: Any | None = None,
    ) -> None:
        """Initialize the orchestrator."""

        if max_workers < 1:
            raise ValueError(
                "max_workers must be at least 1."
            )

        self.agent_handlers = agent_handlers or {}
        self.max_workers = max_workers
        self.agent_run_service = agent_run_service

    # =============================================================
    # MAIN EXECUTION
    # =============================================================

    def execute(
        self,
        plan: ExecutionPlan,
        context: dict[str, Any] | None = None,
    ) -> OrchestrationResult:
        """
        Execute all tasks according to their dependencies.

        Independent ready tasks execute concurrently.

        Agent execution lifecycle:

            PENDING
               ↓
            RUNNING
               ↓
        COMPLETED / FAILED

        If a dependency fails:

            FAILED
               ↓
            BLOCKED dependent task
        """

        # ---------------------------------------------------------
        # Shared context
        # ---------------------------------------------------------

        shared_context = dict(context or {})

        # ---------------------------------------------------------
        # Create execution objects
        # ---------------------------------------------------------

        executions = {
            task.id: TaskExecution(task=task)
            for task in plan.tasks
        }

        # ---------------------------------------------------------
        # Task outputs indexed by task ID
        # ---------------------------------------------------------

        outputs: dict[str, Any] = {}

        # ---------------------------------------------------------
        # Agent run IDs indexed by task ID
        #
        # Example:
        #
        # {
        #     "research_1": "68f....",
        #     "competitor_1": "68f...."
        # }
        # ---------------------------------------------------------

        agent_run_ids: dict[str, str | None] = {}

        # ---------------------------------------------------------
        # Execute DAG
        # ---------------------------------------------------------

        with ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:

            while True:

                # -------------------------------------------------
                # Find pending tasks
                # -------------------------------------------------

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
                # Resolve dependencies
                # -------------------------------------------------

                for execution in pending_tasks:

                    task = execution.task

                    dependency_states = [
                        executions[dependency].status
                        for dependency in task.depends_on
                    ]

                    # ---------------------------------------------
                    # Dependency still pending/running
                    # ---------------------------------------------

                    if any(
                        state in {
                            TaskStatus.PENDING,
                            TaskStatus.RUNNING,
                        }
                        for state in dependency_states
                    ):
                        continue

                    # ---------------------------------------------
                    # Dependency failed/blocked
                    # ---------------------------------------------

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

                        # -----------------------------------------
                        # Persist BLOCKED state
                        # -----------------------------------------

                        self._persist_blocked_run(
                            task=task,
                            context=shared_context,
                            error=execution.error,
                        )

                        progress_made = True
                        continue

                    # ---------------------------------------------
                    # All dependencies completed
                    # ---------------------------------------------

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

                # -------------------------------------------------
                # Future mapping
                #
                # future -> execution
                # -------------------------------------------------

                futures: dict[Any, TaskExecution] = {}

                # -------------------------------------------------
                # Start all ready tasks
                # -------------------------------------------------

                for execution in ready_tasks:

                    task = execution.task
                    agent_name = task.agent.value

                    handler = self.agent_handlers.get(
                        agent_name
                    )

                    # -------------------------------------------------
                    # Build exact task inputs BEFORE execution
                    # -------------------------------------------------

                    task_inputs = self._build_task_inputs(
                        task=task,
                        outputs=outputs,
                        shared_context=shared_context,
                        plan=plan,
                    )

                    # -------------------------------------------------
                    # Missing handler
                    # -------------------------------------------------

                    if handler is None:

                        execution.status = TaskStatus.FAILED
                        execution.error = (
                            f"No handler registered for agent "
                            f"'{agent_name}'."
                        )
                        execution.attempts += 1

                        # ---------------------------------------------
                        # Persist failed execution
                        # ---------------------------------------------

                        run_id = self._persist_start_run(
                            task=task,
                            task_inputs=task_inputs,
                            context=shared_context,
                            attempt=execution.attempts,
                        )

                        agent_run_ids[task.id] = run_id

                        self._persist_failed_run(
                            run_id=run_id,
                            error=execution.error,
                            result=None,
                        )

                        progress_made = True
                        continue

                    # -------------------------------------------------
                    # Mark running
                    # -------------------------------------------------

                    execution.status = TaskStatus.RUNNING
                    execution.attempts += 1

                    # -------------------------------------------------
                    # Persist RUNNING
                    # -------------------------------------------------

                    run_id = self._persist_start_run(
                        task=task,
                        task_inputs=task_inputs,
                        context=shared_context,
                        attempt=execution.attempts,
                    )

                    agent_run_ids[task.id] = run_id

                    # -------------------------------------------------
                    # Execute agent asynchronously
                    # -------------------------------------------------

                    future = executor.submit(
                        self._call_handler,
                        handler,
                        task,
                        task_inputs,
                        shared_context,
                    )

                    futures[future] = execution

                # -------------------------------------------------
                # Collect completed futures
                # -------------------------------------------------

                for future in as_completed(futures):

                    execution = futures[future]
                    task = execution.task

                    run_id = agent_run_ids.get(task.id)

                    try:

                        # ---------------------------------------------
                        # Get agent result
                        # ---------------------------------------------

                        execution.result = future.result()

                        # ---------------------------------------------
                        # Check structured agent failure
                        # ---------------------------------------------

                        result_status = None

                        if isinstance(
                            execution.result,
                            dict,
                        ):
                            result_status = execution.result.get(
                                "status"
                            )

                        # ---------------------------------------------
                        # Agent explicitly returned FAILED
                        # ---------------------------------------------

                        if result_status == "FAILED":

                            execution.status = TaskStatus.FAILED

                            execution.error = (
                                execution.result.get("error")
                                or "Agent execution failed."
                            )

                            # -----------------------------------------
                            # Persist FAILED
                            # -----------------------------------------

                            self._persist_failed_run(
                                run_id=run_id,
                                error=execution.error,
                                result=execution.result,
                            )

                        # ---------------------------------------------
                        # Agent completed successfully
                        # ---------------------------------------------

                        else:

                            execution.status = TaskStatus.COMPLETED

                            # -----------------------------------------
                            # Store output by task ID
                            # -----------------------------------------

                            outputs[
                                task.id
                            ] = execution.result

                            # -----------------------------------------
                            # Store output by agent name
                            #
                            # Example:
                            #
                            # shared_context["research"] = {
                            #     "agent": "research",
                            #     "status": "COMPLETED",
                            #     "data": {...}
                            # }
                            # -----------------------------------------

                            shared_context[
                                task.agent.value
                            ] = execution.result

                            # -----------------------------------------
                            # Extract confidence
                            # -----------------------------------------

                            confidence = None

                            if isinstance(
                                execution.result,
                                dict,
                            ):
                                raw_confidence = (
                                    execution.result.get(
                                        "confidence"
                                    )
                                )

                                if isinstance(
                                    raw_confidence,
                                    (int, float),
                                ):
                                    confidence = float(
                                        raw_confidence
                                    )

                            # -----------------------------------------
                            # Persist COMPLETED
                            # -----------------------------------------

                            self._persist_completed_run(
                                run_id=run_id,
                                result=execution.result,
                                confidence=confidence,
                            )

                    except Exception as exc:

                        # ---------------------------------------------
                        # Python exception from agent
                        # ---------------------------------------------

                        execution.status = TaskStatus.FAILED
                        execution.error = str(exc)

                        # ---------------------------------------------
                        # Persist FAILED
                        # ---------------------------------------------

                        self._persist_failed_run(
                            run_id=run_id,
                            error=execution.error,
                            result=execution.result,
                        )

                    progress_made = True

                # -------------------------------------------------
                # Safety check
                # -------------------------------------------------

                if not progress_made:

                    raise OrchestrationError(
                        "Orchestration could not make progress."
                    )

        # =========================================================
        # FINAL RESULT
        # =========================================================

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
            # AgentAdapter returns:
            #
            # {
            #     "agent": "research",
            #     "status": "COMPLETED",
            #     "summary": "...",
            #     "data": {...}
            # }
            #
            # Downstream agents should receive only "data".
            # -----------------------------------------------------

            if (
                isinstance(
                    dependency_output,
                    dict,
                )
                and dependency_output.get("data") is not None
            ):

                dependency_input = (
                    dependency_output["data"]
                )

            else:

                dependency_input = dependency_output

            # -----------------------------------------------------
            # Expose by task ID
            #
            # inputs["research_1"]
            # -----------------------------------------------------

            inputs[
                dependency_id
            ] = dependency_input

            # -----------------------------------------------------
            # Resolve actual agent name
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

                # ---------------------------------------------
                # Expose by agent name
                #
                # inputs["research"]
                # inputs["competitor"]
                # inputs["seo"]
                # ---------------------------------------------

                inputs[
                    dependency_agent_name
                ] = dependency_input

        # ---------------------------------------------------------
        # 2. Explicit shared-context inputs
        # ---------------------------------------------------------

        for required_input in task.required_inputs:

            if required_input not in shared_context:
                continue

            shared_value = shared_context[
                required_input
            ]

            # -----------------------------------------------------
            # If shared context contains AgentResult wrapper,
            # expose only its data.
            # -----------------------------------------------------

            if (
                isinstance(
                    shared_value,
                    dict,
                )
                and shared_value.get("data") is not None
            ):

                inputs[
                    required_input
                ] = shared_value["data"]

            else:

                inputs[
                    required_input
                ] = shared_value

        # ---------------------------------------------------------
        # 3. Original user request
        # ---------------------------------------------------------

        user_request = shared_context.get(
            "user_request"
        )

        if isinstance(
            user_request,
            str,
        ):
            user_request = user_request.strip()

        if user_request:

            # -----------------------------------------------------
            # Research
            # -----------------------------------------------------

            if (
                "topic" in task.required_inputs
                and "topic" not in inputs
            ):
                inputs["topic"] = user_request

            # -----------------------------------------------------
            # Image / content
            # -----------------------------------------------------

            if (
                "prompt" in task.required_inputs
                and "prompt" not in inputs
            ):
                inputs["prompt"] = user_request

            # -----------------------------------------------------
            # Generic query
            # -----------------------------------------------------

            if (
                "query" in task.required_inputs
                and "query" not in inputs
            ):
                inputs["query"] = user_request

            # -----------------------------------------------------
            # Generic input
            # -----------------------------------------------------

            if (
                "input" in task.required_inputs
                and "input" not in inputs
            ):
                inputs["input"] = user_request

        return inputs

    # =============================================================
    # AGENT RUN PERSISTENCE
    # =============================================================

    def _persist_start_run(
        self,
        task: PlannerTask,
        task_inputs: dict[str, Any],
        context: dict[str, Any],
        attempt: int,
    ) -> str | None:
        """
        Persist RUNNING state.

        Persistence is best-effort.

        If MongoDB is unavailable, the agent should still execute.
        """

        if self.agent_run_service is None:
            return None

        try:

            return self.agent_run_service.start_run(
                user_id=context.get("user_id"),
                conversation_id=context.get(
                    "conversation_id"
                ),
                task_id=task.id,
                agent=task.agent.value,
                input_data=task_inputs,
                attempt=attempt,
            )

        except Exception:
            # Persistence must never stop orchestration.
            return None

    def _persist_completed_run(
        self,
        run_id: str | None,
        result: Any,
        confidence: float | None,
    ) -> None:
        """Persist successful agent execution."""

        if (
            self.agent_run_service is None
            or run_id is None
        ):
            return

        try:

            self.agent_run_service.complete_run(
                run_id=run_id,
                result=result,
                confidence=confidence,
            )

        except Exception:
            # Persistence failure must not affect execution.
            pass

    def _persist_failed_run(
        self,
        run_id: str | None,
        error: str,
        result: Any = None,
    ) -> None:
        """Persist failed agent execution."""

        if (
            self.agent_run_service is None
            or run_id is None
        ):
            return

        try:

            self.agent_run_service.fail_run(
                run_id=run_id,
                error=error,
                result=result,
            )

        except Exception:
            # Persistence failure must not affect execution.
            pass

    def _persist_blocked_run(
        self,
        task: PlannerTask,
        context: dict[str, Any],
        error: str,
    ) -> None:
        """Persist a blocked task."""

        if self.agent_run_service is None:
            return

        try:

            self.agent_run_service.block_run(
                user_id=context.get("user_id"),
                conversation_id=context.get(
                    "conversation_id"
                ),
                task_id=task.id,
                agent=task.agent.value,
                error=error,
            )

        except Exception:
            # Persistence failure must not affect execution.
            pass

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

        if (
            final_execution.status
            == TaskStatus.COMPLETED
        ):
            return final_execution.result

        # ---------------------------------------------------------
        # If final task failed but returned a structured result,
        # preserve that result for debugging/API response.
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # FAILED takes precedence over BLOCKED.
        #
        # Example:
        #
        # research = FAILED
        # competitor = BLOCKED
        #
        # Overall = FAILED
        # ---------------------------------------------------------

        if TaskStatus.FAILED in states:
            return "FAILED"

        if TaskStatus.BLOCKED in states:
            return "BLOCKED"

        if states == {
            TaskStatus.COMPLETED
        }:
            return "COMPLETED"

        return "INCOMPLETE"
