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


    def test_multi_agent_campaign_dag(self):
        execution_order = []

        def research_handler(task, inputs, context):
            execution_order.append("research")

            return {
                "research": "Coffee market research completed",
            }

        def competitor_handler(task, inputs, context):
            execution_order.append("competitor")

            self.assertIn("research", inputs)

            return {
                "competitor": "Competitor analysis completed",
            }

        def seo_handler(task, inputs, context):
            execution_order.append("seo")

            self.assertIn("research", inputs)
            self.assertIn("competitor", inputs)

            return {
                "seo": "SEO analysis completed",
            }

        def content_handler(task, inputs, context):
            execution_order.append("content")

            self.assertIn("research", inputs)
            self.assertIn("competitor", inputs)
            self.assertIn("seo", inputs)

            return {
                "content": "Instagram campaign content generated",
            }

        def image_handler(task, inputs, context):
            execution_order.append("image")

            self.assertIn("content", inputs)

            return {
                "image": "Image generation prepared",
            }

        service = MarketingPipelineService(
            agent_handlers={
                "research": research_handler,
                "competitor": competitor_handler,
                "seo": seo_handler,
                "content": content_handler,
                "image": image_handler,
            }
        )

        result = service.process_request(
            user_request=(
                "Create an Instagram campaign "
                "for my coffee brand"
            ),
            user_id="user123",
            conversation_id="conversation123",
            brand_profile={
                "company_name": "CoffeeOS",
                "industry": "Coffee",
            },
        )

        # ---------------------------------------------------------
        # Intent
        # ---------------------------------------------------------
        self.assertEqual(
            result["intent"]["type"],
            "GENERAL",
        )

        # ---------------------------------------------------------
        # Five-task campaign DAG
        # ---------------------------------------------------------
        self.assertEqual(
            len(result["plan"]["tasks"]),
            5,
        )

        self.assertEqual(
            [task["agent"] for task in result["plan"]["tasks"]],
            [
                "research",
                "competitor",
                "seo",
                "content",
                "image",
            ],
        )

        # ---------------------------------------------------------
        # Complete orchestration
        # ---------------------------------------------------------
        self.assertEqual(
            result["orchestration"]["status"],
            "COMPLETED",
        )

        # ---------------------------------------------------------
        # Dependency order
        # ---------------------------------------------------------
        self.assertEqual(
            execution_order,
            [
                "research",
                "competitor",
                "seo",
                "content",
                "image",
            ],
        )

        # ---------------------------------------------------------
        # All tasks completed
        # ---------------------------------------------------------
        for task_result in result["orchestration"]["tasks"]:
            self.assertEqual(
                task_result["status"],
                "COMPLETED",
            )

        # ---------------------------------------------------------
        # Final output comes from Image Agent
        # ---------------------------------------------------------
        self.assertEqual(
            result["orchestration"]["final_result"]["image"],
            "Image generation prepared",
        )

    def test_image_request_pipeline(self):
        def image_handler(task, inputs, context):
            return {
                "status": "IMAGE_PROVIDER_NOT_CONFIGURED",
                "prompt": context["user_request"],
            }

        service = MarketingPipelineService(
            agent_handlers={
                "image": image_handler,
            }
        )

        result = service.process_request(
            user_request=(
                "Create an Instagram marketing image "
                "for a coffee brand"
            ),
            user_id="user123",
            conversation_id="conversation123",
        )

        self.assertEqual(
            result["intent"]["type"],
            "IMAGE_GENERATION",
        )

        self.assertEqual(
            result["orchestration"]["status"],
            "COMPLETED",
        )

        self.assertEqual(
            result["orchestration"]["final_result"]["status"],
            "IMAGE_PROVIDER_NOT_CONFIGURED",
        )


if __name__ == "__main__":
    unittest.main()