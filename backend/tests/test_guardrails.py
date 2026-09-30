"""Tests for agent guardrails."""

import unittest

from guardrails.schemas import AgentType, GuardrailDecision
from guardrails.service import (
    AgentGuardrailService,
    GuardrailEvaluationError,
)


class TestAgentGuardrailService(unittest.TestCase):
    """Test AgentGuardrailService behavior."""

    def setUp(self) -> None:
        self.service = AgentGuardrailService()

    def test_valid_content_request(self) -> None:
        result = self.service.evaluate(
            AgentType.CONTENT,
            "Create an Instagram caption for my new product.",
        )

        self.assertEqual(
            result.decision,
            GuardrailDecision.VALID,
        )
        self.assertEqual(result.agent, AgentType.CONTENT)

    def test_invalid_content_request(self) -> None:
        result = self.service.evaluate(
            AgentType.CONTENT,
            "What is the capital of India?",
        )

        self.assertEqual(
            result.decision,
            GuardrailDecision.INVALID,
        )

    def test_content_request_needs_clarification(self) -> None:
        result = self.service.evaluate(
            AgentType.CONTENT,
            "Write something",
        )

        self.assertEqual(
            result.decision,
            GuardrailDecision.NEEDS_CLARIFICATION,
        )
        self.assertGreater(
            len(result.missing_information),
            0,
        )

    def test_valid_seo_request(self) -> None:
        result = self.service.evaluate(
            AgentType.SEO,
            "Analyze the SEO of my website.",
        )

        self.assertEqual(
            result.decision,
            GuardrailDecision.VALID,
        )

    def test_seo_request_needs_clarification(self) -> None:
        result = self.service.evaluate(
            AgentType.SEO,
            "Improve my SEO",
        )

        self.assertEqual(
            result.decision,
            GuardrailDecision.NEEDS_CLARIFICATION,
        )
        self.assertIn(
            "website URL, domain, page, or existing SEO context",
            result.missing_information,
        )

    def test_invalid_seo_request(self) -> None:
        result = self.service.evaluate(
            AgentType.SEO,
            "Write me a birthday message.",
        )

        self.assertEqual(
            result.decision,
            GuardrailDecision.INVALID,
        )

    def test_valid_research_request(self) -> None:
        result = self.service.evaluate(
            AgentType.RESEARCH,
            "Research trends in the Indian fitness market.",
        )

        self.assertEqual(
            result.decision,
            GuardrailDecision.VALID,
        )

    def test_valid_competitor_request(self) -> None:
        result = self.service.evaluate(
            AgentType.COMPETITOR,
            "Analyze my competitors and their positioning.",
        )

        self.assertEqual(
            result.decision,
            GuardrailDecision.VALID,
        )

    def test_valid_image_request(self) -> None:
        result = self.service.evaluate(
            AgentType.IMAGE,
            "Create an image for my social media campaign.",
        )

        self.assertEqual(
            result.decision,
            GuardrailDecision.VALID,
        )

    def test_valid_analytics_request(self) -> None:
        result = self.service.evaluate(
            AgentType.ANALYTICS,
            "Show my campaign performance and conversion rate.",
        )

        self.assertEqual(
            result.decision,
            GuardrailDecision.VALID,
        )

    def test_invalid_analytics_request(self) -> None:
        result = self.service.evaluate(
            AgentType.ANALYTICS,
            "Create an Instagram caption for my product.",
        )

        self.assertEqual(
            result.decision,
            GuardrailDecision.INVALID,
        )

    def test_empty_request_raises_error(self) -> None:
        with self.assertRaises(GuardrailEvaluationError):
            self.service.evaluate(
                AgentType.CONTENT,
                "",
            )

    def test_whitespace_request_raises_error(self) -> None:
        with self.assertRaises(GuardrailEvaluationError):
            self.service.evaluate(
                AgentType.SEO,
                "   ",
            )

    def test_confidence_is_within_range(self) -> None:
        result = self.service.evaluate(
            AgentType.CONTENT,
            "Create a LinkedIn post about our new product.",
        )

        self.assertGreaterEqual(result.confidence, 0.0)
        self.assertLessEqual(result.confidence, 1.0)


if __name__ == "__main__":
    unittest.main()