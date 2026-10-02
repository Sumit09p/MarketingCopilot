"""Integration tests for the real MarketingOS agent registry."""

import unittest

from agents.adapter import AgentAdapter
from agents.registry import build_registry
from services.marketing_pipeline_service import MarketingPipelineService


class TestRealAgentPipeline(unittest.TestCase):
    """Verify real agent classes work with the orchestration layer."""

    @staticmethod
    def mock_generate(prompt: str) -> str:
        """
        Return deterministic JSON responses suitable for testing
        the different marketing agents.
        """

        prompt_lower = prompt.lower()

        # ---------------------------------------------------------
        # CONTENT AGENT
        # ---------------------------------------------------------
        if "campaign_hook" in prompt_lower or "hashtags" in prompt_lower:
            return """
            {
                "campaign_hook": "Taste the difference",
                "caption": "Discover premium coffee made for your everyday moments.",
                "cta": "Shop now",
                "hashtags": [
                    "#Coffee",
                    "#PremiumCoffee",
                    "#CoffeeLovers",
                    "#SpecialtyCoffee",
                    "#CoffeeTime"
                ],
                "strategy": [
                    "Highlight product quality",
                    "Target coffee enthusiasts",
                    "Use a strong purchase CTA"
                ]
            }
            """

        # ---------------------------------------------------------
        # COMPETITOR AGENT
        # ---------------------------------------------------------
        if "competitor" in prompt_lower:
            return """
            {
                "competitors": [
                    "Competitor A",
                    "Competitor B"
                ],
                "positioning": "Premium coffee",
                "content_gaps": [
                    "Educational coffee content"
                ],
                "recommendations": [
                    "Emphasize product quality"
                ]
            }
            """

        # ---------------------------------------------------------
        # SEO AGENT
        # ---------------------------------------------------------
        if "seo" in prompt_lower or "keyword" in prompt_lower:
            return """
            {
                "keywords": [
                    "premium coffee",
                    "specialty coffee",
                    "best coffee"
                ],
                "search_intent": "commercial",
                "recommendations": [
                    "Create keyword-focused landing pages"
                ]
            }
            """

        # ---------------------------------------------------------
        # RESEARCH AGENT
        # ---------------------------------------------------------
        if "research" in prompt_lower or "market" in prompt_lower:
            return """
            {
                "topic": "Coffee market",
                "summary": "Qualitative AI-generated research insights for the coffee market.",
                "audience_insights": [
                    "Young professionals value convenient premium coffee options.",
                    "Coffee enthusiasts show interest in specialty and high-quality products.",
                    "Consumers may respond to strong product storytelling and lifestyle positioning."
                ],
                "market_trends": [
                    "Growing interest in specialty coffee experiences.",
                    "Increasing adoption of convenient coffee subscription models.",
                    "Social media is an important channel for coffee discovery and engagement."
                ],
                "opportunities": [
                    "Position premium coffee around quality and convenience.",
                    "Use social content to educate and engage coffee enthusiasts.",
                    "Explore subscription-oriented offerings for repeat customers."
                ]
            }
            """

        # ---------------------------------------------------------
        # DEFAULT RESPONSE
        # ---------------------------------------------------------
        return """
        {
            "result": "Mock agent analysis completed"
        }
        """

    # =============================================================
    # TEST 1: REGISTRY
    # =============================================================

    def test_registry_contains_real_agents(self):
        """Verify all expected marketing agents exist."""

        registry = build_registry(self.mock_generate)

        expected_agents = {
            "research",
            "competitor",
            "seo",
            "content",
            "analytics",
            "recommendation",
            "image",
        }

        self.assertTrue(
            expected_agents.issubset(registry.keys())
        )

    # =============================================================
    # TEST 2: RESEARCH AGENT
    # =============================================================

    def test_real_research_agent_through_adapter(self):
        """Verify ResearchAgent works through AgentAdapter."""

        registry = build_registry(self.mock_generate)

        handler = AgentAdapter(
            registry["research"]
        )

        result = handler(
            task=type(
                "Task",
                (),
                {
                    "id": "research_test",
                    "agent": "research",
                },
            )(),
            inputs={
                "topic": "Coffee market",
                "product": "Premium coffee",
            },
            context={
                "user_request": "Research the coffee market",
                "brand_profile": {
                    "company_name": "CoffeeOS",
                    "industry": "Coffee",
                },
            },
        )

        self.assertEqual(
            result["agent"],
            "research",
        )

        self.assertEqual(
            result["status"],
            "COMPLETED",
        )

        self.assertIsNotNone(
            result["data"]
        )

        self.assertEqual(
            result["data"]["topic"],
            "Coffee market",
        )

        self.assertEqual(
            len(result["data"]["audience_insights"]),
            3,
        )

        self.assertEqual(
            len(result["data"]["market_trends"]),
            3,
        )

        self.assertEqual(
            len(result["data"]["opportunities"]),
            3,
        )

    # =============================================================
    # TEST 3: CONTENT AGENT
    # =============================================================

    def test_real_content_agent_through_adapter(self):
        """Verify ContentAgent works through AgentAdapter."""

        registry = build_registry(self.mock_generate)

        handler = AgentAdapter(
            registry["content"]
        )

        result = handler(
            task=type(
                "Task",
                (),
                {
                    "id": "content_test",
                    "agent": "content",
                },
            )(),
            inputs={
                "product_name": "CoffeeOS Premium Coffee",
                "description": (
                    "Premium specialty coffee for "
                    "everyday coffee lovers."
                ),
                "target_audience": (
                    "Young professionals and coffee enthusiasts"
                ),
                "platform": "Instagram",
                "tone": "Premium and friendly",
            },
            context={
                "user_request": (
                    "Create an Instagram caption "
                    "for my coffee product"
                ),
                "brand_profile": {
                    "company_name": "CoffeeOS",
                    "industry": "Coffee",
                },
            },
        )

        self.assertEqual(
            result["agent"],
            "content",
        )

        self.assertEqual(
            result["status"],
            "COMPLETED",
        )

        self.assertIn(
            "caption",
            result["data"],
        )

    # =============================================================
    # TEST 4: REAL AGENTS THROUGH PIPELINE
    # =============================================================

    def test_pipeline_can_use_real_agent_adapters(self):
        """
        Verify the central MarketingPipelineService can execute
        a real registered agent through AgentAdapter.
        """

        registry = build_registry(
            self.mock_generate
        )

        handlers = {
            name: AgentAdapter(agent)
            for name, agent in registry.items()
        }

        service = MarketingPipelineService(
            agent_handlers=handlers
        )

        result = service.process_request(
            user_request=(
                "Research market trends "
                "for the coffee industry"
            ),
            user_id="test-user",
            conversation_id="test-conversation",
            brand_profile={
                "company_name": "CoffeeOS",
                "industry": "Coffee",
            },
        )

        self.assertEqual(
            result["intent"]["type"],
            "RESEARCH",
        )

        self.assertEqual(
            result["orchestration"]["status"],
            "COMPLETED",
        )

        self.assertEqual(
            result["orchestration"]["final_result"]["agent"],
            "research",
        )

        self.assertEqual(
            result["orchestration"]["final_result"]["status"],
            "COMPLETED",
        )


if __name__ == "__main__":
    unittest.main()