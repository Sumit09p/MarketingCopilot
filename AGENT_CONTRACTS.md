# MarketingOS AI — Agent Contracts

## 1. Purpose

This document defines the responsibilities, inputs, outputs, dependencies, validation rules, and boundaries of every specialized AI agent.

The agents are:

1. Research Agent
2. Competitor Analysis Agent
3. SEO Agent
4. Content Generation Agent
5. Image Generation Agent
6. Analytics / Marketing Insights Agent

Every agent MUST follow its contract.

An agent MUST NOT perform another agent's primary responsibility.

---

# 2. Common Agent Architecture

All agents follow:

```text
Request
   ↓
Agent Input Validation
   ↓
Agent
   ↓
LLM / External Service if required
   ↓
Structured Output
   ↓
Output Validation
   ↓
Orchestrator