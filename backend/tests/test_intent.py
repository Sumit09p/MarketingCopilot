"""Tests for intent detection."""

import unittest

from intent.schemas import IntentType
from intent.service import IntentDetectionError, IntentDetectionService


class TestIntentDetectionService(unittest.TestCase):
    """Test IntentDetectionService behavior."""

    def setUp(self) -> None:
        self.service = IntentDetectionService()

    def test_content_generation_intent(self) -> None:
        result = self.service.detect(
            "Create an Instagram caption for my new product."
        )

        self.assertEqual(
            result.intent,
            IntentType.CONTENT_GENERATION,
        )
        self.assertGreaterEqual(result.confidence, 0.9)

    def test_seo_intent(self) -> None:
        result = self.service.detect(
            "Analyze my website SEO and suggest keywords."
        )

        self.assertEqual(
            result.intent,
            IntentType.SEO_ANALYSIS,
        )

    def test_competitor_analysis_intent(self) -> None:
        result = self.service.detect(
            "Analyze my competitors and their positioning."
        )

        self.assertEqual(
            result.intent,
            IntentType.COMPETITOR_ANALYSIS,
        )

    def test_research_intent(self) -> None:
        result = self.service.detect(
            "Research current trends in the fitness market."
        )

        self.assertEqual(
            result.intent,
            IntentType.RESEARCH,
        )

    def test_image_generation_intent(self) -> None:
        result = self.service.detect(
            "Generate an image for my social media campaign."
        )

        self.assertEqual(
            result.intent,
            IntentType.IMAGE_GENERATION,
        )

    def test_analytics_intent(self) -> None:
        result = self.service.detect(
            "Show me the campaign performance and conversion rate."
        )

        self.assertEqual(
            result.intent,
            IntentType.ANALYTICS,
        )

    def test_general_intent(self) -> None:
        result = self.service.detect(
            "What can you help me with?"
        )

        self.assertEqual(
            result.intent,
            IntentType.GENERAL,
        )

    def test_empty_input_raises_error(self) -> None:
        with self.assertRaises(IntentDetectionError):
            self.service.detect("")

    def test_whitespace_input_raises_error(self) -> None:
        with self.assertRaises(IntentDetectionError):
            self.service.detect("   ")

    def test_confidence_is_valid(self) -> None:
        result = self.service.detect(
            "Create a LinkedIn post."
        )

        self.assertGreaterEqual(result.confidence, 0.0)
        self.assertLessEqual(result.confidence, 1.0)


if __name__ == "__main__":
    unittest.main()