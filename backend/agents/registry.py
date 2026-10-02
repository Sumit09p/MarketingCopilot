from __future__ import annotations

from .image_agent import ImageAgent
from .analytics_agent import AnalyticsAgent
from .base import GenerateFn
from .competitor_agent import CompetitorAgent
from .content_agent import ContentAgent
from .research_agent import ResearchAgent
from .seo_agent import SEOAgent
from .recommendation_agent import RecommendationAgent

def build_registry(generate: GenerateFn) -> dict:
    """Canonical agent names used by the orchestrator / API: content, research, competitor, seo, analytics."""
    return {
        "content": ContentAgent(generate),
        "research": ResearchAgent(generate),
        "competitor": CompetitorAgent(generate),
        "seo": SEOAgent(generate),
        "analytics": AnalyticsAgent(generate),
        "recommendation": RecommendationAgent(generate),
        "image": ImageAgent(generate),
    }


def get_agent(name: str, generate: GenerateFn):
    registry = build_registry(generate)
    agent = registry.get(name)
    if agent is None:
        raise KeyError(f"Unknown agent '{name}'. Known agents: {', '.join(registry)}.")
    return agent
