"""Tests for planner schemas, plan validation, and planner service."""

import unittest

from guardrails.schemas import AgentType
from planner.schemas import ExecutionPlan, PlannerTask
from planner.service import PlannerService
from planner.validator import PlanValidationError, PlanValidator


class TestPlanValidator(unittest.TestCase):
    """Test PlanValidator behavior."""

    def setUp(self) -> None:
        self.validator = PlanValidator()

    def test_valid_single_task_plan(self) -> None:
        plan = ExecutionPlan(
            goal="Research the fitness market.",
            tasks=[
                PlannerTask(
                    id="research_1",
                    agent=AgentType.RESEARCH,
                )
            ],
        )

        result = self.validator.validate(plan)

        self.assertEqual(result.goal, plan.goal)
        self.assertEqual(len(result.tasks), 1)

    def test_valid_dependency_plan(self) -> None:
        plan = ExecutionPlan(
            goal="Create a marketing campaign.",
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
                    depends_on=["research_1", "competitor_1"],
                    required_inputs=[
                        "research",
                        "competitor",
                    ],
                ),
            ],
        )

        result = self.validator.validate(plan)

        self.assertEqual(len(result.tasks), 3)

    def test_duplicate_task_ids_are_rejected(self) -> None:
        plan = ExecutionPlan(
            goal="Test duplicate IDs.",
            tasks=[
                PlannerTask(
                    id="task_1",
                    agent=AgentType.RESEARCH,
                ),
                PlannerTask(
                    id="task_1",
                    agent=AgentType.CONTENT,
                ),
            ],
        )

        with self.assertRaises(PlanValidationError):
            self.validator.validate(plan)

    def test_unknown_dependency_is_rejected(self) -> None:
        plan = ExecutionPlan(
            goal="Test unknown dependency.",
            tasks=[
                PlannerTask(
                    id="content_1",
                    agent=AgentType.CONTENT,
                    depends_on=["research_99"],
                ),
            ],
        )

        with self.assertRaises(PlanValidationError):
            self.validator.validate(plan)

    def test_self_dependency_is_rejected(self) -> None:
        plan = ExecutionPlan(
            goal="Test self dependency.",
            tasks=[
                PlannerTask(
                    id="research_1",
                    agent=AgentType.RESEARCH,
                    depends_on=["research_1"],
                ),
            ],
        )

        with self.assertRaises(PlanValidationError):
            self.validator.validate(plan)

    def test_circular_dependency_is_rejected(self) -> None:
        plan = ExecutionPlan(
            goal="Test circular dependency.",
            tasks=[
                PlannerTask(
                    id="research_1",
                    agent=AgentType.RESEARCH,
                    depends_on=["content_1"],
                ),
                PlannerTask(
                    id="content_1",
                    agent=AgentType.CONTENT,
                    depends_on=["research_1"],
                ),
            ],
        )

        with self.assertRaises(PlanValidationError):
            self.validator.validate(plan)

    def test_three_task_cycle_is_rejected(self) -> None:
        plan = ExecutionPlan(
            goal="Test three task cycle.",
            tasks=[
                PlannerTask(
                    id="research_1",
                    agent=AgentType.RESEARCH,
                    depends_on=["content_1"],
                ),
                PlannerTask(
                    id="content_1",
                    agent=AgentType.CONTENT,
                    depends_on=["image_1"],
                ),
                PlannerTask(
                    id="image_1",
                    agent=AgentType.IMAGE,
                    depends_on=["research_1"],
                ),
            ],
        )

        with self.assertRaises(PlanValidationError):
            self.validator.validate(plan)

    def test_empty_dependency_id_is_rejected(self) -> None:
        plan = ExecutionPlan(
            goal="Test empty dependency.",
            tasks=[
                PlannerTask(
                    id="content_1",
                    agent=AgentType.CONTENT,
                    depends_on=[""],
                ),
            ],
        )

        with self.assertRaises(PlanValidationError):
            self.validator.validate(plan)

    def test_empty_task_id_is_rejected(self) -> None:
        plan = ExecutionPlan(
            goal="Test empty task ID.",
            tasks=[
                PlannerTask(
                    id="   ",
                    agent=AgentType.RESEARCH,
                ),
            ],
        )

        with self.assertRaises(PlanValidationError):
            self.validator.validate(plan)

    def test_empty_goal_is_rejected(self) -> None:
        plan = ExecutionPlan(
            goal="   ",
            tasks=[
                PlannerTask(
                    id="research_1",
                    agent=AgentType.RESEARCH,
                ),
            ],
        )

        with self.assertRaises(PlanValidationError):
            self.validator.validate(plan)

    def test_more_than_maximum_tasks_is_rejected(self) -> None:
        tasks = [
            PlannerTask(
                id=f"task_{index}",
                agent=AgentType.RESEARCH,
            )
            for index in range(21)
        ]

        plan = ExecutionPlan(
            goal="Test maximum task limit.",
            tasks=tasks,
        )

        with self.assertRaises(PlanValidationError):
            self.validator.validate(plan)

    def test_independent_tasks_are_valid(self) -> None:
        plan = ExecutionPlan(
            goal="Run independent marketing analysis.",
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

        result = self.validator.validate(plan)

        self.assertEqual(len(result.tasks), 2)

    def test_long_dependency_chain_is_valid(self) -> None:
        plan = ExecutionPlan(
            goal="Test dependency chain.",
            tasks=[
                PlannerTask(
                    id="research_1",
                    agent=AgentType.RESEARCH,
                ),
                PlannerTask(
                    id="competitor_1",
                    agent=AgentType.COMPETITOR,
                    depends_on=["research_1"],
                ),
                PlannerTask(
                    id="seo_1",
                    agent=AgentType.SEO,
                    depends_on=["competitor_1"],
                ),
                PlannerTask(
                    id="content_1",
                    agent=AgentType.CONTENT,
                    depends_on=["seo_1"],
                ),
                PlannerTask(
                    id="image_1",
                    agent=AgentType.IMAGE,
                    depends_on=["content_1"],
                ),
            ],
        )

        result = self.validator.validate(plan)

        self.assertEqual(len(result.tasks), 5)


class TestPlannerService(unittest.TestCase):
    """Test PlannerService behavior."""

    def setUp(self) -> None:
        self.planner = PlannerService()

    def test_empty_input_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.planner.create_plan("")

    def test_whitespace_input_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.planner.create_plan("   ")

    def test_research_plan(self) -> None:
        plan = self.planner.create_plan(
            "Research the Indian fitness market.",
            intent="RESEARCH",
        )

        self.assertEqual(len(plan.tasks), 1)
        self.assertEqual(
            plan.tasks[0].agent,
            AgentType.RESEARCH,
        )
        self.assertEqual(
            plan.tasks[0].id,
            "research_1",
        )

    def test_competitor_plan(self) -> None:
        plan = self.planner.create_plan(
            "Analyze my competitors.",
            intent="COMPETITOR_ANALYSIS",
        )

        self.assertEqual(len(plan.tasks), 1)
        self.assertEqual(
            plan.tasks[0].agent,
            AgentType.COMPETITOR,
        )
        self.assertEqual(
            plan.tasks[0].id,
            "competitor_1",
        )

    def test_seo_plan(self) -> None:
        plan = self.planner.create_plan(
            "Analyze my website SEO.",
            intent="SEO_ANALYSIS",
        )

        self.assertEqual(len(plan.tasks), 1)
        self.assertEqual(
            plan.tasks[0].agent,
            AgentType.SEO,
        )
        self.assertEqual(
            plan.tasks[0].id,
            "seo_1",
        )

    def test_content_plan(self) -> None:
        plan = self.planner.create_plan(
            "Create an Instagram caption.",
            intent="CONTENT_GENERATION",
        )

        self.assertEqual(len(plan.tasks), 1)
        self.assertEqual(
            plan.tasks[0].agent,
            AgentType.CONTENT,
        )
        self.assertEqual(
            plan.tasks[0].id,
            "content_1",
        )

    def test_image_plan(self) -> None:
        plan = self.planner.create_plan(
            "Create a marketing image.",
            intent="IMAGE_GENERATION",
        )

        self.assertEqual(len(plan.tasks), 1)
        self.assertEqual(
            plan.tasks[0].agent,
            AgentType.IMAGE,
        )
        self.assertEqual(
            plan.tasks[0].id,
            "image_1",
        )

    def test_analytics_plan(self) -> None:
        plan = self.planner.create_plan(
            "Show campaign performance.",
            intent="ANALYTICS",
        )

        self.assertEqual(len(plan.tasks), 1)
        self.assertEqual(
            plan.tasks[0].agent,
            AgentType.ANALYTICS,
        )
        self.assertEqual(
            plan.tasks[0].id,
            "analytics_1",
        )

    def test_campaign_plan_contains_expected_agents(self) -> None:
        plan = self.planner.create_plan(
            "Create an Instagram campaign for my product.",
        )

        agents = [
            task.agent
            for task in plan.tasks
        ]

        self.assertEqual(
            agents,
            [
                AgentType.RESEARCH,
                AgentType.COMPETITOR,
                AgentType.SEO,
                AgentType.CONTENT,
                AgentType.IMAGE,
            ],
        )

    def test_campaign_plan_contains_five_tasks(self) -> None:
        plan = self.planner.create_plan(
            "Create a marketing campaign.",
        )

        self.assertEqual(len(plan.tasks), 5)

    def test_campaign_research_has_no_dependencies(self) -> None:
        plan = self.planner.create_plan(
            "Create a marketing campaign.",
        )

        research_task = plan.tasks[0]

        self.assertEqual(
            research_task.id,
            "research_1",
        )
        self.assertEqual(
            research_task.depends_on,
            [],
        )

    def test_campaign_competitor_depends_on_research(self) -> None:
        plan = self.planner.create_plan(
            "Create a marketing campaign.",
        )

        competitor_task = plan.tasks[1]

        self.assertEqual(
            competitor_task.id,
            "competitor_1",
        )
        self.assertEqual(
            competitor_task.depends_on,
            ["research_1"],
        )

    def test_campaign_seo_dependencies(self) -> None:
        plan = self.planner.create_plan(
            "Create a marketing campaign.",
        )

        seo_task = plan.tasks[2]

        self.assertEqual(
            seo_task.id,
            "seo_1",
        )
        self.assertEqual(
            seo_task.depends_on,
            [
                "research_1",
                "competitor_1",
            ],
        )

    def test_campaign_content_dependencies(self) -> None:
        plan = self.planner.create_plan(
            "Create a marketing campaign.",
        )

        content_task = plan.tasks[3]

        self.assertEqual(
            content_task.id,
            "content_1",
        )
        self.assertEqual(
            content_task.depends_on,
            [
                "research_1",
                "competitor_1",
                "seo_1",
            ],
        )

    def test_campaign_image_depends_on_content(self) -> None:
        plan = self.planner.create_plan(
            "Create a marketing campaign.",
        )

        image_task = plan.tasks[4]

        self.assertEqual(
            image_task.id,
            "image_1",
        )
        self.assertEqual(
            image_task.depends_on,
            ["content_1"],
        )

    def test_campaign_plan_passes_validator(self) -> None:
        plan = self.planner.create_plan(
            "Create a marketing campaign.",
        )

        validator = PlanValidator()
        validated_plan = validator.validate(plan)

        self.assertEqual(
            len(validated_plan.tasks),
            5,
        )

    def test_unsupported_request_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.planner.create_plan(
                "Tell me a random joke.",
            )

    def test_lowercase_intent_is_supported(self) -> None:
        plan = self.planner.create_plan(
            "Create an Instagram caption.",
            intent="content_generation",
        )

        self.assertEqual(
            plan.tasks[0].agent,
            AgentType.CONTENT,
        )

    def test_mixed_case_intent_is_supported(self) -> None:
        plan = self.planner.create_plan(
            "Analyze my website SEO.",
            intent="Seo_Analysis",
        )

        self.assertEqual(
            plan.tasks[0].agent,
            AgentType.SEO,
        )


if __name__ == "__main__":
    unittest.main()