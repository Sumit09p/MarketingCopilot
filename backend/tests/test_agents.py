from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from backend.agents.analytics_agent import AnalyticsAgent
from backend.agents.competitor_agent import CompetitorAgent
from backend.agents.content_agent import ContentAgent
from backend.agents.recommendation_agent import RecommendationAgent
from backend.agents.research_agent import ResearchAgent
from backend.agents.seo_agent import SEOAgent
from backend.rag.retriever import SemanticRetriever


CONTENT_OK = {
    "campaign_hook": "Fuel your first PR.",
    "caption": "Start your gym journey with a whey protein made for beginners.",
    "cta": "Ask your trainer if this fits your routine.",
    "hashtags": ["#Fitness", "#GymBeginner", "#Protein", "#CampusLife", "#Wellness"],
    "strategy": [
        "Post a beginner workout carousel.",
        "Collaborate with campus fitness clubs.",
        "Share a weekly habit-building story series.",
    ],
}

def test_recommendation_successful_generation():
    payload = {
        "recommendations": [
            "Create beginner-focused content.",
            "Test campus fitness partnerships.",
            "Improve landing-page messaging.",
        ],
        "priority_actions": [
            "Launch the beginner content series.",
            "Test the highest-priority landing-page change.",
        ],
    }

    agent = RecommendationAgent(lambda prompt: json.dumps(payload))

    result = agent.run(
        "recommendation_1",
        {
            "research": {
                "summary": "Beginner audiences need simple educational content."
            },
            "competitor": {
                "recommendations": ["Focus on beginner positioning."]
            },
            "seo": {
                "recommendations": ["Create beginner-focused FAQ content."]
            },
            "content": {
                "campaign_hook": "Start your fitness journey."
            },
            "analytics": {
                "metrics": {
                    "ctr": 10.0,
                    "conversion_rate": 20.0,
                }
            },
        },
    )

    assert result.status == "COMPLETED"
    assert result.agent == "recommendation"
    assert len(result.data["recommendations"]) == 3
    assert len(result.data["priority_actions"]) == 2


def test_recommendation_invalid_json():
    agent = RecommendationAgent(lambda prompt: "not-json")

    result = agent.run(
        "recommendation_2",
        {"research": {"summary": "Some research"}},
    )

    assert result.status == "FAILED"
    assert "invalid JSON" in (result.error or "")


def test_recommendation_wrong_count():
    payload = {
        "recommendations": [
            "Only one recommendation"
        ],
        "priority_actions": [
            "Action one",
            "Action two",
        ],
    }

    agent = RecommendationAgent(lambda prompt: json.dumps(payload))

    result = agent.run(
        "recommendation_3",
        {"research": {"summary": "Some research"}},
    )

    assert result.status == "FAILED"
    assert "3 recommendations" in (result.error or "")


def test_content_successful_generation():
    agent = ContentAgent(lambda prompt: json.dumps(CONTENT_OK))
    result = agent.run(
        "content_1",
        {
            "product_name": "Protein Powder",
            "description": "A whey protein supplement designed for fitness enthusiasts.",
            "target_audience": "Gym beginners and college students",
            "platform": "Instagram",
            "tone": "Energetic",
        },
    )
    assert result.status == "COMPLETED"
    assert result.agent == "content"
    assert result.data["campaign_hook"] == CONTENT_OK["campaign_hook"]
    assert len(result.data["hashtags"]) == 5
    assert len(result.data["strategy"]) == 3


def test_content_missing_input():
    agent = ContentAgent(lambda prompt: json.dumps(CONTENT_OK))
    result = agent.run(
        "content_2",
        {
            "product_name": "Protein Powder",
            "description": "A whey protein supplement.",
            "target_audience": "Students",
            "platform": "Instagram",
        },
    )
    assert result.status == "FAILED"
    assert result.data is None
    assert "tone" in (result.error or "")


def test_content_invalid_json():
    agent = ContentAgent(lambda prompt: "not-json")
    result = agent.run(
        "content_3",
        {
            "product_name": "Protein Powder",
            "description": "A whey protein supplement.",
            "target_audience": "Students",
            "platform": "Instagram",
            "tone": "Energetic",
        },
    )
    assert result.status == "FAILED"
    assert "invalid JSON" in (result.error or "")


def test_content_incorrect_hashtag_count():
    bad = dict(CONTENT_OK)
    bad["hashtags"] = ["#One", "#Two"]
    agent = ContentAgent(lambda prompt: json.dumps(bad))
    result = agent.run(
        "content_4",
        {
            "product_name": "Protein Powder",
            "description": "A whey protein supplement.",
            "target_audience": "Students",
            "platform": "Instagram",
            "tone": "Energetic",
        },
    )
    assert result.status == "FAILED"
    assert "5 hashtags" in (result.error or "")


def test_research_successful_structured_result():
    payload = {
        "topic": "Protein Powder",
        "summary": "AI-generated research insights for beginner fitness nutrition.",
        "audience_insights": ["Students want affordable habits.", "Beginners fear complexity.", "Social proof matters."],
        "market_trends": ["Campus fitness content is growing.", "Short-form education performs well.", "Clean-label language is common."],
        "opportunities": ["Beginner education series.", "Club partnerships.", "Routine-building content."],
    }
    agent = ResearchAgent(lambda prompt: json.dumps(payload))
    result = agent.run("research_1", {"topic": "Protein Powder", "target_audience": "Students", "industry": "Fitness"})
    assert result.status == "COMPLETED"
    assert result.data["topic"] == "Protein Powder"
    assert len(result.data["audience_insights"]) == 3
    assert len(result.data["market_trends"]) == 3
    assert len(result.data["opportunities"]) == 3


def test_competitor_successful_structured_result():
    payload = {
        "competitors": ["Brand A", "Brand B"],
        "strengths": ["Clear beginner positioning"],
        "weaknesses": ["Little campus-specific content"],
        "content_opportunities": ["Student routine walkthroughs"],
        "recommendations": ["Compare usage occasions, not invented market share"],
    }
    agent = CompetitorAgent(lambda prompt: json.dumps(payload))
    result = agent.run(
        "competitor_1",
        {"product": "Protein Powder", "competitors": ["Brand A", "Brand B"], "industry": "Fitness"},
    )
    assert result.status == "COMPLETED"
    assert result.data["competitors"] == ["Brand A", "Brand B"]
    assert result.data["recommendations"]


def test_seo_successful_structured_result():
    payload = {
        "primary_keywords": ["beginner protein powder"],
        "secondary_keywords": ["campus gym nutrition"],
        "search_intent": "informational",
        "meta_title": "Beginner Protein Powder Guide",
        "meta_description": "Qualitative SEO suggestions for beginner protein content.",
        "content_gaps": ["No beginner dosage-education page"],
        "recommendations": ["Write a FAQ without inventing search volume"],
    }
    agent = SEOAgent(lambda prompt: json.dumps(payload))
    result = agent.run(
        "seo_1",
        {
            "topic": "Protein Powder",
            "product": "Protein Powder",
            "target_audience": "Students",
            "content": "Homepage copy only",
        },
    )
    assert result.status == "COMPLETED"
    assert result.data["search_intent"] == "informational"
    assert result.data["primary_keywords"]


def test_analytics_metrics_and_zero_denominators():
    agent = AnalyticsAgent(
        lambda prompt: json.dumps(
            {
                "insights": ["CTR is healthy for this spend level.", "Conversion rate can still improve.", "ROAS is positive."],
                "recommendations": ["Protect high-CTR ads.", "Test landing pages.", "Scale slowly."],
            }
        )
    )
    result = agent.run(
        "analytics_1",
        {
            "impressions": 100,
            "clicks": 10,
            "conversions": 2,
            "spend": 50,
            "revenue": 200,
        },
    )
    assert result.status == "COMPLETED"
    metrics = result.data["metrics"]
    assert metrics["ctr"] == 10.0
    assert metrics["conversion_rate"] == 20.0
    assert metrics["cpc"] == 5.0
    assert metrics["cpa"] == 25.0
    assert metrics["roas"] == 4.0

    zero = AnalyticsAgent(lambda prompt: json.dumps({"insights": ["n/a"], "recommendations": ["n/a"]}))
    zero_result = zero.run(
        "analytics_2",
        {
            "impressions": 0,
            "clicks": 0,
            "conversions": 0,
            "spend": 0,
            "revenue": 0,
        },
    )
    assert zero_result.status == "COMPLETED"
    zero_metrics = zero_result.data["metrics"]
    assert zero_metrics["ctr"] is None
    assert zero_metrics["conversion_rate"] is None
    assert zero_metrics["cpc"] is None
    assert zero_metrics["cpa"] is None
    assert zero_metrics["roas"] is None


def test_rag_semantic_retrieval():
    retriever = SemanticRetriever(
        chunk_size=10,
        chunk_overlap=2,
    )

    text = (
        "Our brand voice is warm, simple, friendly, and student-focused. "
        "We communicate with students using clear and approachable language. "
        "Our campaigns should remain helpful and easy to understand."
    )

    chunk_count = retriever.add_document(
        "brand.txt",
        text,
    )

    assert chunk_count == 4

    results = retriever.retrieve(
        "friendly student communication",
        top_k=2,
    )

    assert len(results) == 2
    assert results[0]["source"] == "brand.txt"
    assert results[0]["score"] > 0
    assert results[0]["chunk_id"] >= 0


def test_rag_empty_query():
    retriever = SemanticRetriever()

    retriever.add_document(
        "brand.txt",
        "Our brand voice is friendly and student-focused.",
    )

    results = retriever.retrieve("")

    assert results == []


def test_rag_invalid_document():
    retriever = SemanticRetriever()

    try:
        retriever.add_document("", "Some document text.")
        assert False
    except ValueError:
        assert True


def test_rag_persistence(tmp_path):
    retriever = SemanticRetriever(
        chunk_size=10,
        chunk_overlap=2,
    )

    retriever.add_document(
        "brand.txt",
        "Our brand voice is friendly and student-focused.",
    )

    storage_path = tmp_path / "rag_index"

    retriever.save(storage_path)

    loaded_retriever = SemanticRetriever(
        chunk_size=10,
        chunk_overlap=2,
    )

    loaded_retriever.load(storage_path)

    results = loaded_retriever.retrieve(
        "student friendly communication",
        top_k=1,
    )

    assert len(results) == 1
    assert results[0]["source"] == "brand.txt"