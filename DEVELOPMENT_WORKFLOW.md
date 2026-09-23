# MarketingOS AI — Development Workflow

## 1. Purpose

This document defines how the three team members develop MarketingOS AI together.

The goal is:

- Parallel development
- Minimal Git conflicts
- Clear ownership
- Stable architecture
- Controlled Cursor/AI usage
- Easy integration
- No accidental rewriting of another member's work

---

# 2. Team Structure

## Member 1 — Backend + AI Core

Owns:

- FastAPI foundation
- MongoDB
- Authentication
- LLM service
- Intent detection
- Agent guardrails
- Planner
- Plan Validator
- Orchestrator
- Shared Context
- Backend integration
- API integration

Primary directories:

```text
backend/routes/
backend/services/
backend/guardrails/
backend/orchestrator/
backend/schemas/
backend/models/
backend/utils/