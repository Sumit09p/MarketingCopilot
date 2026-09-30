import unittest

from services.marketing_pipeline_service import (
    MarketingPipelineService,
)


class TestMarketingPipelineService(unittest.TestCase):

    def test_research_request_pipeline(self):
        def research_handler(task, inputs, context):
            return {
                "topic": context["user_request"],
                "result": "Research completed",
            }

        service = MarketingPipelineService(
            agent_handlers={
                "research": research_handler,
            }
        )

        result = service.process_request(
            user_request="Research market trends for AI marketing",
            user_id="user123",
            conversation_id="conversation123",
            brand_profile={
                "company_name": "Test Company",
                "industry": "Technology",
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
            result["orchestration"]["tasks"][0]["status"],
            "COMPLETED",
        )

        self.assertEqual(
            result["orchestration"]["final_result"]["result"],
            "Research completed",
        )

    def test_content_request_pipeline(self):
        def content_handler(task, inputs, context):
            return {
                "content": "Sample Instagram caption",
            }

        service = MarketingPipelineService(
            agent_handlers={
                "content": content_handler,
            }
        )

        result = service.process_request(
            user_request="Create an Instagram caption for my product",
            user_id="user123",
        )

        self.assertEqual(
            result["intent"]["type"],
            "CONTENT_GENERATION",
        )

        self.assertEqual(
            result["orchestration"]["status"],
            "COMPLETED",
        )

        self.assertEqual(
            result["orchestration"]["final_result"]["content"],
            "Sample Instagram caption",
        )

    def test_brand_profile_reaches_agent(self):
        received = {}

        def research_handler(task, inputs, context):
            received["brand_profile"] = context["brand_profile"]

            return {
                "status": "ok",
            }

        service = MarketingPipelineService(
            agent_handlers={
                "research": research_handler,
            }
        )

        service.process_request(
            user_request="Research the market trends",
            brand_profile={
                "company_name": "MarketingOS",
                "industry": "SaaS",
            },
        )

        self.assertEqual(
            received["brand_profile"]["company_name"],
            "MarketingOS",
        )

        self.assertEqual(
            received["brand_profile"]["industry"],
            "SaaS",
        )


if __name__ == "__main__":
    unittest.main()