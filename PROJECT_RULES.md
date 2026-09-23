# MarketingOS AI — Project Rules

## 1. Project Identity

Project Name: MarketingOS AI

Project Type:
Agentic AI-powered digital marketing workspace.

Core Goal:
Build a working digital marketing platform that combines:
- Generative AI
- Specialized AI agents
- Agent orchestration
- RAG / knowledge retrieval
- Brand-specific memory
- Guardrails
- Campaign management
- Marketing analytics
- External marketing integrations

This project MUST NOT become a simple chatbot or a collection of unrelated LLM API calls.

---

## 2. Core Architecture

The application follows this high-level flow:

User
  ↓
React Frontend
  ↓
FastAPI Backend
  ↓
Request Analyzer / Intent Detection
  ↓
 ┌───────────────────────────────┐
 │ General Request               │
 │ → Planner                     │
 │                               │
 │ Explicit Agent Selected       │
 │ → Agent Guardrail             │
 └───────────────────────────────┘
  ↓
Planner / Validated Decision
  ↓
Plan Validator
  ↓
Python Orchestrator
  ↓
Specialized Agents
  ↓
Shared Context
  ↓
Output Validation
  ↓
Final Response
  ↓
React Frontend

---

## 3. Technology Stack

### Backend
- Python 3.13.x
- FastAPI
- Uvicorn
- MongoDB
- PyMongo
- Pydantic
- JWT authentication
- bcrypt/password hashing

### Frontend
- React
- Vite
- JavaScript
- React Router
- Recharts
- Normal CSS

DO NOT introduce Tailwind CSS unless explicitly approved.

### AI
The application must use a provider abstraction for LLM access.

The exact LLM provider may change.

LLM provider configuration MUST come from environment variables.

Never hard-code API keys.

### RAG
Preferred approach:
- Local/open-source embeddings
- FAISS or Chroma
- PyMuPDF for PDF extraction
- python-docx for DOCX extraction

### Deployment
Preferred:
- Frontend → Vercel
- Backend → Render
- Database → MongoDB Atlas

The system should remain usable within available free tiers where possible.

---

## 4. Python Environment

Required Python version:

Python 3.13.x

Current development environment:

Python 3.13.15

All team members MUST use the same Python version.

Backend virtual environment:

backend/.venv/

However, the project root may contain the local development environment during initial setup.

Virtual environments MUST NOT be committed to Git.

Never change the project's Python version without team agreement.

---

## 5. Backend Architecture

There MUST be ONE FastAPI backend.

Do NOT create separate backend servers for individual agents.

Backend responsibilities include:

backend/
├── main.py
├── models/
├── schemas/
├── routes/
├── services/
├── agents/
├── guardrails/
├── orchestrator/
├── utils/
└── tests/

### Ownership

Backend/Core:
- routes/
- services/
- guardrails/
- orchestrator/
- main.py
- database/configuration

AI Agents:
- agents/

Frontend:
- frontend/

Agents communicate through defined Python interfaces/contracts.

---

## 6. Specialized Agents

The system will contain these specialized agents:

1. Research Agent
2. Competitor Analysis Agent
3. SEO Agent
4. Content Generation Agent
5. Image Generation Agent
6. Analytics / Marketing Insights Agent

Each agent MUST have:
- Clear responsibility
- Defined input
- Defined output
- Validation
- Error handling
- No responsibility outside its domain

Agents MUST NOT silently perform another agent's responsibilities.

---

## 7. Planner Rules

The Planner answers:

"What should the system do?"

The Planner may determine:
- Which agents are required
- Task order
- Dependencies
- Parallel execution opportunities
- Required inputs
- Optional tasks

The Planner should produce a structured plan.

Example:

{
  "goal": "Create Instagram campaign",
  "tasks": [
    {
      "id": "research_1",
      "agent": "research",
      "depends_on": []
    },
    {
      "id": "competitor_1",
      "agent": "competitor",
      "depends_on": ["research_1"]
    },
    {
      "id": "seo_1",
      "agent": "seo",
      "depends_on": ["research_1", "competitor_1"]
    },
    {
      "id": "content_1",
      "agent": "content",
      "depends_on": [
        "research_1",
        "competitor_1",
        "seo_1"
      ]
    }
  ]
}

The Planner MUST NOT directly execute Python code or external tools.

The Planner only proposes structured decisions.

Python code validates and executes the plan.

---

## 8. Guardrail Rules

Planner and Guardrail are different components.

Planner:
"What should the system do?"

Guardrail:
"Is this request appropriate for the selected agent?"

When a user explicitly selects an agent:

VALID:
→ execute the appropriate agent.

INVALID:
→ reject or redirect the request.

NEEDS_CLARIFICATION:
→ ask the user for missing information.
→ DO NOT execute the agent.

Examples:

Content Agent + "Create an Instagram caption"
→ VALID

Content Agent + "What is the capital of India?"
→ INVALID

Content Agent + "Make something good"
→ NEEDS_CLARIFICATION

SEO Agent + "Analyze my website SEO"
→ VALID

SEO Agent + "Write birthday wishes"
→ INVALID

SEO Agent + "Improve my SEO"
→ NEEDS_CLARIFICATION if no website/context is available.

Guardrails MUST execute before an explicitly selected specialized agent.

---

## 9. Orchestrator Rules

The Python Orchestrator controls execution.

The Orchestrator is responsible for:
- Dependency resolution
- Task ordering
- Parallel execution
- Passing outputs between agents
- Retry handling
- Failure handling
- Required/optional task handling
- Execution state
- Final control flow

Possible task states:

PENDING
RUNNING
COMPLETED
FAILED
BLOCKED

The Orchestrator MUST validate the task graph before execution.

Circular dependencies MUST be rejected.

Example:

Research
   ↓
Competitor
   ├──→ SEO
   └──→ Content
          ↓
        Image

SEO and Content may execute in parallel when their dependencies are satisfied.

---

## 10. LLM Safety Rules

LLMs may:
- Understand user intent
- Generate structured plans
- Generate content
- Interpret retrieved information
- Provide recommendations
- Generate agent outputs

LLMs MUST NOT directly:
- Execute Python code
- Execute shell commands
- Modify files
- Access databases directly
- Call arbitrary APIs directly
- Bypass validation
- Control application flow without Python validation

Python code MUST control execution.

All structured LLM outputs MUST be validated before use.

---

## 11. Shared Context

Agents may receive relevant shared context.

Shared context can contain:
- User request
- Brand profile
- Campaign information
- Research results
- Competitor results
- SEO results
- Content results
- Retrieved knowledge
- Relevant analytics

Do NOT pass unnecessary huge context to every agent.

Only relevant information should be provided to each agent.

---

## 12. Brand Profile

The Brand Profile may contain:

- Company name
- Industry
- Website
- Company description
- Location
- Target audience
- Audience demographics
- Audience interests
- Audience pain points
- Brand voice
- Brand tone
- USP
- Products/services
- Competitors
- Marketing goals

Agents should use the Brand Profile when relevant.

---

## 13. RAG Rules

RAG pipeline:

Upload document
→ Extract text
→ Clean text
→ Chunk text
→ Generate embeddings
→ Store vectors
→ Retrieve relevant chunks
→ Provide relevant context to agent/LLM

Supported document types may include:
- PDF
- TXT
- DOCX
- Company documents
- Brand guidelines
- Product catalogs
- Pricing documents
- Previous campaigns

Do NOT send every document to the LLM.

Retrieve only relevant information.

Where possible, outputs should identify the source document.

---

## 14. Database Rules

MongoDB is the primary database.

Expected collections include:

- users
- companies
- brand_profiles
- conversations
- messages
- campaigns
- agent_runs
- documents
- knowledge_chunks
- integrations
- analytics

Database access MUST be centralized through backend services.

Agents MUST NOT independently create database connections.

Never hard-code database credentials.

---

## 15. Authentication Rules

Authentication must use secure password hashing.

Passwords MUST NOT be stored in plain text.

JWT secrets MUST come from environment variables.

Never commit:
- passwords
- JWT secrets
- API keys
- OAuth secrets
- database credentials

---

## 16. External Integrations

External marketing platforms must use official APIs/OAuth where applicable.

Never ask users to provide external service passwords.

Never fake a successful integration.

If an integration is unavailable:

Show a clear state such as:

"Not Connected"

or

"Coming Soon"

Demo/sample data MUST be clearly labeled as sample/demo data.

---

## 17. Analytics Rules

Deterministic calculations should be performed by Python.

Examples:
- CTR
- Conversion rate
- ROI
- Revenue totals
- Engagement rate

LLMs may interpret the calculated data and generate insights.

Do NOT ask the LLM to perform calculations that Python can reliably perform.

---

## 18. Code Quality Rules

Write readable and maintainable code.

Prefer:
- Small functions
- Clear names
- Type hints
- Pydantic schemas
- Modular services
- Explicit error handling

Avoid:
- Giant files
- Giant functions
- Duplicate logic
- Hard-coded secrets
- Global mutable state
- Unnecessary abstractions

---

## 19. Dependency Rules

Before installing a package:

1. Check whether it already exists in requirements.txt.
2. Check whether the functionality can be implemented with existing dependencies.
3. Only install a package when necessary.
4. Explain why a new dependency is required.
5. Update requirements.txt intentionally.

Do NOT randomly install packages.

Do NOT change Python versions to solve dependency problems without approval.

---

## 20. AI Coding Agent Rules

When using Cursor or another AI coding agent:

The agent MUST:

1. Read PROJECT_RULES.md first.
2. Read relevant architecture/contract documents.
3. Understand existing code before modifying it.
4. Modify only the requested module.
5. Preserve existing working functionality.
6. Avoid unnecessary rewrites.
7. Avoid creating duplicate files or duplicate services.
8. Avoid changing unrelated modules.
9. Reuse existing utilities where appropriate.
10. Report files created/modified.
11. Report tests performed.
12. Report remaining issues.

The agent MUST NOT:

- Rewrite the entire project
- Change the architecture without approval
- Create another backend
- Create another database layer
- Create duplicate agents
- Replace working code unnecessarily
- Install random dependencies
- Invent APIs
- Invent integrations
- Hard-code secrets
- Delete working functionality without explicit permission

---

## 21. Module Isolation

When implementing a feature, work only within the relevant module.

Example:

If implementing SEO Agent:

Allowed:
- agents/seo/
- relevant schemas
- relevant tests

Not allowed without approval:
- Authentication rewrite
- Frontend redesign
- Database architecture rewrite
- Planner rewrite
- Deployment changes

---

## 22. Existing Code Preservation

Before modifying a file:

- Read the existing file.
- Understand its purpose.
- Preserve working behavior.
- Make the smallest required change.

Never replace a complete file simply because rewriting it is easier.

---

## 23. Error Handling

Failures must be explicit.

Do not silently ignore errors.

Agent failures should provide:
- Agent name
- Task ID
- Error message
- Execution status

The system should distinguish:

FAILED
from
BLOCKED

A blocked task is one whose dependency failed or is unavailable.

---

## 24. Testing

Every major module must have basic tests.

Minimum testing expectations:

- Authentication
- Intent detection
- Guardrails
- Planner
- Plan validation
- Orchestrator
- Agent execution
- RAG retrieval
- API endpoints

Test the smallest unit before integrating larger modules.

---

## 25. Git Rules

Use feature branches.

Examples:

feature/auth
feature/chat-ui
feature/research-agent
feature/planner
feature/rag

Do not randomly push incomplete work directly to main.

Before committing:

1. Check git status.
2. Test the changed module.
3. Review the changes.
4. Commit with a meaningful message.

Example:

feat: add research agent

fix: validate planner dependencies

feat: add chat history API

---

## 26. Team Development Rules

There are three development tracks.

### Member 1 — Backend + AI Core

Owns:
- FastAPI
- Database
- Authentication
- LLM service
- Intent detection
- Guardrails
- Planner
- Plan validator
- Orchestrator
- Shared context
- Backend integration

### Member 2 — Frontend + Product

Owns:
- React
- Authentication UI
- Main layout
- Chat
- Chat history
- Brand profile
- Agent selection
- Campaign workspace
- Dashboard
- Calendar
- Knowledge UI
- Integration UI
- Workflow visualization

### Member 3 — AI Agents + RAG + Analytics

Owns:
- Agent framework
- Research Agent
- Competitor Agent
- SEO Agent
- Content Agent
- Image Agent
- RAG pipeline
- Knowledge retrieval
- Analytics Agent
- Agent testing

Member 3 MUST NOT create a second backend.

All three tracks integrate with the ONE FastAPI backend.

---

## 27. Mock Development

Team members may use mock data/interfaces while another module is incomplete.

Example:

Frontend may initially use:

GET /api/chat/mock

while backend chat logic is being developed.

AI agents may initially use mock planner/context objects.

Mocks MUST be clearly marked and replaced during integration.

Do not leave fake production behavior accidentally enabled.

---

## 28. No Hallucinated Features

If a requested feature depends on an unavailable external API:

Do NOT pretend it works.

Instead:
- Implement the interface.
- Provide a graceful fallback.
- Clearly indicate unavailable functionality.
- Use sample data only when explicitly marked as demo/sample.

---

## 29. Environment Variables

Secrets belong in:

.env

Never commit .env.

Commit:

.env.example

The .env.example file must contain variable names but no real secrets.

---

## 30. Definition of Done

A feature is considered complete only when:

- Code is implemented.
- Existing functionality still works.
- Required validation exists.
- Errors are handled.
- Basic tests pass.
- Dependencies are documented.
- No secrets are committed.
- No unrelated files were modified.
- The feature follows the architecture.
- Git changes are reviewed.

---

## 31. Most Important Rule

DO NOT optimize for writing the most code.

Optimize for:

Correct architecture
+
Small modules
+
Reliable execution
+
Clear contracts
+
Testable behavior
+
Maintainability

The project must demonstrate a real agentic AI architecture, not merely a chatbot connected to an LLM API.