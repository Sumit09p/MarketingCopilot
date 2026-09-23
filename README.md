# MarketingOS AI

An agentic AI-powered digital marketing workspace that combines Generative AI, specialized marketing agents, RAG, dependency-aware orchestration, guardrails, brand memory, campaign management, and marketing analytics.

---

## Project Overview

MarketingOS AI provides a ChatGPT-like conversational workspace for digital marketing.

The system can:

- Understand marketing requests
- Detect user intent
- Select appropriate AI agents
- Validate explicit agent requests using guardrails
- Create dependency-aware execution plans
- Execute multiple specialized agents
- Maintain brand-specific context
- Retrieve information from uploaded documents
- Generate marketing content
- Generate marketing creatives when supported
- Analyze campaign performance
- Manage campaigns and content calendars
- Connect to supported marketing platforms

---

## Specialized Agents

The system contains:

1. Research Agent
2. Competitor Analysis Agent
3. SEO Agent
4. Content Generation Agent
5. Image Generation Agent
6. Analytics / Marketing Insights Agent

---

## Architecture

```text
User
 |
 v
React Frontend
 |
 v
FastAPI Backend
 |
 v
Intent Detection
 |
 +----------------------+
 |                      |
 v                      v
General Request     Explicit Agent
 |                      |
 v                      v
Planner             Guardrail
 |                  /    |    \
 v               VALID INVALID CLARIFY
Plan Validator       |      |      |
 |                   |      |      |
 v                   |      |      |
Orchestrator <-------+      |      |
 |                          |      |
 v                          v      v
Specialized Agents       Reject   Ask
 |
 v
Shared Context
 |
 v
Output Validation
 |
 v
Final Response
 |
 v
React Frontend