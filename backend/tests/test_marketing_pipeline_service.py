import unittest

from services.marketing_pipeline_service import (
    MarketingPipelineService,
)


class FakeKnowledgeService:
    """
    Fake RAG service used only for testing.

    This avoids MongoDB / FAISS / embedding model access
    during the pipeline unit test.
    """

    def __init__(self):
        self.calls = []

    def search(
        self,
        user_id,
        query,
        top_k=3,
        min_score=0.0,
    ):
        self.calls.append(
            {
                "user_id": user_id,
                "query": query,
                "top_k": top_k,
                "min_score": min_score,
            }
        )

        return [
            {
                "source": "brand.txt",
                "text": (
                    "MarketingOS targets small businesses "
                    "with affordable digital marketing."
                ),
                "score": 0.93,
                "chunk_id": 0,
            }
        ]


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

        self.assertEqual(
            result["intent"]["type"],
            "GENERAL",
        )

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

        self.assertEqual(
            result["orchestration"]["status"],
            "COMPLETED",
        )

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

        for task_result in result["orchestration"]["tasks"]:
            self.assertEqual(
                task_result["status"],
                "COMPLETED",
            )

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

    def test_knowledge_reaches_agent(self):
        received = {}

        def research_handler(task, inputs, context):
            received["knowledge"] = context["knowledge"]

            return {
                "status": "ok",
            }

        service = MarketingPipelineService(
            agent_handlers={
                "research": research_handler,
            }
        )

        knowledge = [
            {
                "source": "brand.txt",
                "text": (
                    "Our brand targets small businesses "
                    "with affordable digital marketing."
                ),
                "score": 0.91,
                "chunk_id": 0,
            }
        ]

        service.process_request(
            user_request="Research my target market",
            user_id="user123",
            knowledge=knowledge,
        )

        self.assertEqual(
            len(received["knowledge"]),
            1,
        )

        self.assertEqual(
            received["knowledge"][0]["source"],
            "brand.txt",
        )

        self.assertIn(
            "small businesses",
            received["knowledge"][0]["text"],
        )

    def test_automatic_rag_retrieval(self):
        """
        Verify that the pipeline automatically calls the
        KnowledgeService when knowledge is not manually supplied.
        """

        received = {}

        def research_handler(task, inputs, context):
            received["knowledge"] = context["knowledge"]

            return {
                "status": "research_completed",
            }

        fake_knowledge_service = FakeKnowledgeService()

        service = MarketingPipelineService(
            agent_handlers={
                "research": research_handler,
            },
            knowledge_service=fake_knowledge_service,
        )

        user_request = (
            "Research my target market and understand "
            "our small business customers"
        )

        result = service.process_request(
            user_request=user_request,
            user_id="user123",
            conversation_id="conversation123",
        )

        # ---------------------------------------------------------
        # Verify KnowledgeService.search() was called
        # ---------------------------------------------------------

        self.assertEqual(
            len(fake_knowledge_service.calls),
            1,
        )

        self.assertEqual(
            fake_knowledge_service.calls[0]["user_id"],
            "user123",
        )

        self.assertEqual(
            fake_knowledge_service.calls[0]["query"],
            user_request,
        )

        self.assertEqual(
            fake_knowledge_service.calls[0]["top_k"],
            5,
        )

        # ---------------------------------------------------------
        # Verify retrieved knowledge reached the agent
        # ---------------------------------------------------------

        self.assertEqual(
            len(received["knowledge"]),
            1,
        )

        self.assertEqual(
            received["knowledge"][0]["source"],
            "brand.txt",
        )

        self.assertIn(
            "small business",
            received["knowledge"][0]["text"],
        )

        # ---------------------------------------------------------
        # Verify pipeline completed normally
        # ---------------------------------------------------------

        self.assertEqual(
            result["orchestration"]["status"],
            "COMPLETED",
        )

        # ---------------------------------------------------------
        # Verify RAG metadata is present in final response
        # ---------------------------------------------------------

        self.assertEqual(
            result["knowledge"]["retrieved"],
            1,
        )

        self.assertEqual(
            result["knowledge"]["sources"],
            ["brand.txt"],
        )

    def test_automatic_brand_profile_retrieval(self):
        """
        Verify that the pipeline automatically retrieves the saved
        brand profile when no brand_profile is manually supplied.
        """

        received = {}

        def research_handler(task, inputs, context):
            received["brand_profile"] = context["brand_profile"]

            return {
                "status": "research_completed",
            }

        class FakeBrandProfileService:
            def __init__(self):
                self.calls = []

            def get_brand_profile(self, user_id):
                self.calls.append(user_id)

                return {
                    "id": "brand123",
                    "user_id": user_id,
                    "company_name": "CoffeeOS",
                    "industry": "Coffee",
                    "description": "Premium coffee brand",
                    "target_audience": "Young professionals",
                    "products_services": ["Coffee", "Cold Brew"],
                    "brand_tone": "Premium and friendly",
                    "website": "https://coffeeos.example",
                    "location": "Mumbai",
                    "competitors": ["BrandA", "BrandB"],
                    "social_links": {
                        "instagram": "https://instagram.com/coffeeos"
                    },
                }

        fake_brand_profile_service = FakeBrandProfileService()

        service = MarketingPipelineService(
            agent_handlers={
                "research": research_handler,
            },
            brand_profile_service=fake_brand_profile_service,
        )

        result = service.process_request(
            user_request="Research the coffee market trends",
            user_id="user123",
            conversation_id="conversation123",
        )

        # ---------------------------------------------------------
        # Verify BrandProfileService was called automatically
        # ---------------------------------------------------------

        self.assertEqual(
            fake_brand_profile_service.calls,
            ["user123"],
        )

        # ---------------------------------------------------------
        # Verify retrieved brand profile reached the agent
        # ---------------------------------------------------------

        self.assertEqual(
            received["brand_profile"]["company_name"],
            "CoffeeOS",
        )

        self.assertEqual(
            received["brand_profile"]["industry"],
            "Coffee",
        )

        self.assertEqual(
            received["brand_profile"]["target_audience"],
            "Young professionals",
        )

        # ---------------------------------------------------------
        # Verify pipeline completed normally
        # ---------------------------------------------------------

        self.assertEqual(
            result["orchestration"]["status"],
            "COMPLETED",
        )

        # ---------------------------------------------------------
        # Verify brand profile metadata is present
        # ---------------------------------------------------------

        self.assertTrue(
            result["brand_profile"]["loaded"]
        )

        self.assertEqual(
            result["brand_profile"]["company_name"],
            "CoffeeOS",
        )

        self.assertEqual(
            result["brand_profile"]["industry"],
            "Coffee",
        )


if __name__ == "__main__":
    unittest.main()