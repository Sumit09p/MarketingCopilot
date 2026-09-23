# MarketingOS AI — System Architecture

## 1. System Overview

MarketingOS AI is an agentic AI-powered digital marketing workspace.

The system provides:

- ChatGPT-like conversational interaction
- Intent detection
- Central planning
- Specialized AI agents
- Dependency-aware orchestration
- Agent guardrails
- Brand-specific memory
- RAG / knowledge retrieval
- Campaign management
- Marketing analytics
- External integrations
- AI-generated marketing content and creatives

The system is designed as a modular monolithic application for the FYP.

There is ONE backend application.

There are NOT separate microservices for each agent.

---

# 2. High-Level Architecture

```text
                         USER
                           |
                           v
                  +----------------+
                  | React Frontend |
                  +----------------+
                           |
                           | HTTP / JSON
                           v
                  +----------------+
                  | FastAPI Backend|
                  +----------------+
                           |
                           v
               +-----------------------+
               | Request Analyzer      |
               | / Intent Detection    |
               +-----------------------+
                    /              \
                   /                \
                  v                  v
        General Request       Explicit Agent
                  |                  |
                  v                  v
             +---------+      +-------------+
             | Planner |      | Agent       |
             |         |      | Guardrail   |
             +---------+      +-------------+
                  |             /      |      \
                  |           VALID INVALID CLARIFY
                  |             |       |      |
                  |             |       |      |
                  +-------------+       |      |
                        |               |      |
                        v               v      v
                +----------------+    Reject  Ask User
                | Plan Validator |
                +----------------+
                        |
                        v
                +----------------+
                | Orchestrator   |
                +----------------+
                        |
          +-------------+-------------+
          |             |             |
          v             v             v
     Research      Competitor       SEO
       Agent         Agent          Agent
          |             |             |
          +-------------+-------------+
                        |
                        v
                  Content Agent
                        |
                        v
                   Image Agent
                        |
                        v
                 Output Validator
                        |
                        v
                  Final Response
                        |
                        v
                  React Frontend