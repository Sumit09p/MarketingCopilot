"""Validation logic for planner execution plans."""

from backend.planner.schemas import ExecutionPlan


class PlanValidationError(Exception):
    """Raised when an execution plan is invalid."""


class PlanValidator:
    """Validate planner-generated execution plans."""

    MAX_TASKS = 20

    def validate(self, plan: ExecutionPlan) -> ExecutionPlan:
        """
        Validate an execution plan.

        The validator checks:
        - task count
        - unique task IDs
        - dependency references
        - self-dependencies
        - circular dependencies
        - required task fields
        """

        if not plan.goal.strip():
            raise PlanValidationError(
                "Execution plan goal cannot be empty."
            )

        if not plan.tasks:
            raise PlanValidationError(
                "Execution plan must contain at least one task."
            )

        if len(plan.tasks) > self.MAX_TASKS:
            raise PlanValidationError(
                f"Execution plan cannot contain more than "
                f"{self.MAX_TASKS} tasks."
            )

        self._validate_task_ids(plan)
        self._validate_dependencies(plan)
        self._validate_cycles(plan)

        return plan

    @staticmethod
    def _validate_task_ids(plan: ExecutionPlan) -> None:
        """Validate that task IDs are present and unique."""

        task_ids = [task.id.strip() for task in plan.tasks]

        if any(not task_id for task_id in task_ids):
            raise PlanValidationError(
                "Every task must have a non-empty ID."
            )

        if len(task_ids) != len(set(task_ids)):
            raise PlanValidationError(
                "Task IDs must be unique."
            )

    @staticmethod
    def _validate_dependencies(plan: ExecutionPlan) -> None:
        """Validate dependency references and self-dependencies."""

        task_ids = {task.id for task in plan.tasks}

        for task in plan.tasks:
            for dependency in task.depends_on:
                if not dependency.strip():
                    raise PlanValidationError(
                        f"Task '{task.id}' contains an empty dependency ID."
                    )

                if dependency not in task_ids:
                    raise PlanValidationError(
                        f"Task '{task.id}' depends on unknown task "
                        f"'{dependency}'."
                    )

                if dependency == task.id:
                    raise PlanValidationError(
                        f"Task '{task.id}' cannot depend on itself."
                    )

    @staticmethod
    def _validate_cycles(plan: ExecutionPlan) -> None:
        """Detect circular dependencies using depth-first search."""

        graph = {
            task.id: task.depends_on
            for task in plan.tasks
        }

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(task_id: str) -> None:
            if task_id in visiting:
                raise PlanValidationError(
                    "Execution plan contains a circular dependency."
                )

            if task_id in visited:
                return

            visiting.add(task_id)

            for dependency in graph[task_id]:
                visit(dependency)

            visiting.remove(task_id)
            visited.add(task_id)

        for task_id in graph:
            visit(task_id)
