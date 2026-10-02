from agents.registry import build_registry
from agents.adapter import AgentAdapter
from orchestrator.service import OrchestratorService
from planner.service import PlannerService


# ---------------------------------------------------------
# MOCK LLM
# ---------------------------------------------------------

def mock_generate(prompt: str) -> str:
    """
    Deterministic mock LLM for DAG integration testing.

    Returns valid JSON according to the exact contract
    expected by each marketing agent.
    """

    prompt_lower = prompt.lower()

    # -----------------------------------------------------
    # Research Agent
    # -----------------------------------------------------

    if (
        "marketing research assistant" in prompt_lower
        or (
            "audience_insights" in prompt_lower
            and "market_trends" in prompt_lower
            and "opportunities" in prompt_lower
        )
    ):
        return """
        {
            "topic": "Fitness App",
            "summary": "Qualitative AI-generated research indicates that a fitness app focused on college students can emphasize affordability, convenience, and mobile-first experiences.",
            "audience_insights": [
                "College students prefer affordable and convenient fitness solutions.",
                "Students frequently engage with fitness content on social media.",
                "Mobile-first experiences are useful for students with busy schedules."
            ],
            "market_trends": [
                "AI-powered fitness recommendations",
                "Short-form fitness and workout content",
                "Affordable and personalized fitness plans"
            ],
            "opportunities": [
                "Student-focused fitness plans",
                "Social media fitness campaigns",
                "Personalized beginner-friendly workout recommendations"
            ]
        }
        """

    # -----------------------------------------------------
    # Competitor Agent
    # -----------------------------------------------------

    if (
        "competitor analysis assistant" in prompt_lower
        or (
            "content_opportunities" in prompt_lower
            and "recommendations" in prompt_lower
            and "competitors" in prompt_lower
        )
    ):
        return """
        {
            "competitors": [
                "MyFitnessPal",
                "Fitbit",
                "Nike Training Club"
            ],
            "strengths": [
                "Strong brand recognition",
                "Large fitness content libraries",
                "Established mobile applications"
            ],
            "weaknesses": [
                "Limited student-specific positioning",
                "Some advanced features require paid plans",
                "Less focus on college communities"
            ],
            "content_opportunities": [
                "College student fitness guides",
                "Short-form workout content",
                "Affordable student fitness challenges"
            ],
            "recommendations": [
                "Position the product around student affordability",
                "Build a strong social media presence for student communities",
                "Create personalized beginner-friendly fitness content"
            ]
        }
        """

    # -----------------------------------------------------
    # SEO Agent
    # -----------------------------------------------------

    if (
        "seo recommendation assistant" in prompt_lower
        or (
            "primary_keywords" in prompt_lower
            and "secondary_keywords" in prompt_lower
            and "search_intent" in prompt_lower
        )
    ):
        return """
        {
            "primary_keywords": [
                "fitness app for college students",
                "student fitness app"
            ],
            "secondary_keywords": [
                "college workout app",
                "affordable fitness app",
                "student workout app"
            ],
            "search_intent": "Informational and commercial intent focused on finding affordable fitness solutions designed for college students.",
            "meta_title": "Best Fitness App for College Students",
            "meta_description": "Discover an affordable fitness app designed for college students with personalized workouts, practical fitness guidance, and student-friendly features.",
            "content_gaps": [
                "Student-specific fitness guides",
                "Affordable workout plans for college students",
                "Beginner fitness content for busy students"
            ],
            "recommendations": [
                "Create student-focused landing pages",
                "Publish fitness guides targeting college students",
                "Optimize content around student fitness keywords"
            ]
        }
        """

    # -----------------------------------------------------
    # Content Agent
    # -----------------------------------------------------

    if (
        "campaign_hook" in prompt_lower
        or (
            "content" in prompt_lower
            and "caption" in prompt_lower
            and "hashtags" in prompt_lower
        )
    ):
        return """
        {
            "campaign_hook": "Stay fit without breaking your student budget.",
            "caption": "College life is busy, but staying healthy does not have to be difficult. Discover simple workouts and personalized fitness guidance designed for students.",
            "cta": "Download the app and start your fitness journey today.",
            "hashtags": [
                "#CollegeFitness",
                "#StudentFitness",
                "#FitnessApp",
                "#HealthyStudents"
            ],
            "strategy": [
                "Use short-form social content focused on affordable fitness.",
                "Highlight practical workouts designed for busy college students.",
                "Use student-focused messaging to build community engagement."
            ]
        }
        """

    # -----------------------------------------------------
    # Image Agent
    # -----------------------------------------------------

    if (
        "image generation" in prompt_lower
        or "image prompt" in prompt_lower
    ):
        return """
        {
            "prompt": "A modern college student using a fitness app on a smartphone while exercising in a university gym, energetic digital marketing campaign style.",
            "image_url": null,
            "provider": null
        }
        """

    # -----------------------------------------------------
    # Fallback
    # -----------------------------------------------------

    return """
    {
        "summary": "Generic mock response for DAG integration testing."
    }
    """


# ---------------------------------------------------------
# 1. Build REAL agent registry
# ---------------------------------------------------------

registry = build_registry(mock_generate)


print("\n")
print("=" * 70)
print("REGISTERED AGENTS")
print("=" * 70)

for name in registry:
    print("-", name)


# ---------------------------------------------------------
# 2. Create orchestrator handlers
# ---------------------------------------------------------

handlers = {
    name: AgentAdapter(agent)
    for name, agent in registry.items()
}


# ---------------------------------------------------------
# 3. Create orchestrator
# ---------------------------------------------------------

orchestrator = OrchestratorService(
    agent_handlers=handlers,
    max_workers=4,
)


# ---------------------------------------------------------
# 4. Create planner
# ---------------------------------------------------------

planner = PlannerService()


# ---------------------------------------------------------
# 5. Campaign request
# ---------------------------------------------------------

user_request = (
    "I want to launch a digital marketing campaign "
    "for a new fitness app targeting college students. "
    "Research the market, analyze competitors, "
    "suggest SEO strategy, create social media content, "
    "and generate a suitable campaign image."
)


# ---------------------------------------------------------
# 6. Create execution plan
# ---------------------------------------------------------

plan = planner.create_plan(user_request)


print("\n")
print("=" * 70)
print("CAMPAIGN DAG")
print("=" * 70)

for task in plan.tasks:
    print(
        f"{task.id:15} | "
        f"agent={task.agent.value:15} | "
        f"depends_on={task.depends_on}"
    )


# ---------------------------------------------------------
# 7. Execute DAG
# ---------------------------------------------------------

context = {
    "user_request": user_request
}

result = orchestrator.execute(
    plan=plan,
    context=context,
)


# ---------------------------------------------------------
# 8. Print execution results
# ---------------------------------------------------------

print("\n")
print("=" * 70)
print("EXECUTION RESULTS")
print("=" * 70)

for execution in result.tasks:

    print("\n")
    print(f"TASK       : {execution.task.id}")
    print(f"AGENT      : {execution.task.agent.value}")
    print(f"STATUS     : {execution.status}")
    print(f"ATTEMPTS   : {execution.attempts}")

    if execution.error:
        print(f"ERROR      : {execution.error}")

    if execution.result:
        print("RESULT:")
        print(execution.result)


# ---------------------------------------------------------
# 9. Overall result
# ---------------------------------------------------------

print("\n")
print("=" * 70)
print("OVERALL RESULT")
print("=" * 70)

print(f"STATUS      : {result.status}")

print("\nFINAL RESULT:")
print(result.final_result)

print("=" * 70)