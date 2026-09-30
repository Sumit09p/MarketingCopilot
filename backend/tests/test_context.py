import unittest

from context.schemas import SharedContext
from context.service import SharedContextService


class TestSharedContext(unittest.TestCase):

    def test_create_context(self):
        service = SharedContextService()

        context = service.create_context(
            user_request="Create an Instagram campaign",
            user_id="user123",
            conversation_id="conv123",
            brand_profile={
                "company_name": "Test Company",
                "industry": "Technology",
            },
        )

        self.assertEqual(
            context.user_request,
            "Create an Instagram campaign",
        )

        self.assertEqual(
            context.user_id,
            "user123",
        )

        self.assertEqual(
            context.brand_profile["company_name"],
            "Test Company",
        )

    def test_add_and_get_agent_output(self):
        service = SharedContextService()

        context = service.create_context(
            user_request="Analyze competitors",
        )

        service.add_agent_output(
            context=context,
            agent="research",
            output={
                "competitors": [
                    "Company A",
                    "Company B",
                ]
            },
        )

        result = service.get_agent_output(
            context=context,
            agent="research",
        )

        self.assertEqual(
            result["competitors"],
            ["Company A", "Company B"],
        )

    def test_get_missing_agent_output(self):
        service = SharedContextService()

        context = service.create_context(
            user_request="Test request",
        )

        result = service.get_agent_output(
            context=context,
            agent="research",
        )

        self.assertIsNone(result)

    def test_get_filtered_agent_inputs(self):
        service = SharedContextService()

        context = service.create_context(
            user_request="Create a marketing campaign",
            brand_profile={
                "company_name": "Test Company",
            },
            knowledge=[
                {
                    "source": "brand_guidelines.pdf",
                    "content": "Use a professional tone.",
                }
            ],
        )

        service.add_agent_output(
            context=context,
            agent="research",
            output={
                "market": "Technology",
            },
        )

        inputs = service.get_agent_inputs(
            context=context,
            required_inputs=[
                "user_request",
                "brand_profile",
                "research",
            ],
        )

        self.assertEqual(
            inputs["user_request"],
            "Create a marketing campaign",
        )

        self.assertEqual(
            inputs["brand_profile"]["company_name"],
            "Test Company",
        )

        self.assertEqual(
            inputs["research"]["market"],
            "Technology",
        )

        self.assertNotIn(
            "knowledge",
            inputs,
        )


if __name__ == "__main__":
    unittest.main()