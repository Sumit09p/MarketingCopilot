# MarketingOS AI — API Contract

## 1. Purpose

This document defines the communication contract between:

Frontend
↕
FastAPI Backend

The frontend and backend must follow these request and response structures.

The API contract should remain stable once implementation begins.

If a contract must change, update this document first and inform all team members.

---

# 2. Base URL

Development:

http://localhost:8000

Production:

Configured through frontend environment variables.

The frontend MUST NOT hard-code production URLs inside components.

---

# 3. API Prefix

All application APIs should use:

/api

Examples:

/api/auth/login

/api/chat

/api/brand

/api/campaigns

---

# 4. Standard Response Format

Successful responses should follow a predictable structure where appropriate.

Example:

{
  "success": true,
  "data": {},
  "message": null
}

Error:

{
  "success": false,
  "data": null,
  "message": "Error message"
}

Not every endpoint must artificially wrap naturally structured responses, but the response structure must remain predictable.

---

# 5. Authentication

## Register

### Endpoint

POST /api/auth/register

### Request

{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "password"
}

### Response

{
  "success": true,
  "data": {
    "user": {
      "id": "user_id",
      "name": "John Doe",
      "email": "john@example.com"
    }
  },
  "message": "Registration successful"
}

---

# 6. Login

### Endpoint

POST /api/auth/login

### Request

{
  "email": "john@example.com",
  "password": "password"
}

### Response

{
  "success": true,
  "data": {
    "access_token": "jwt_token",
    "token_type": "bearer",
    "user": {
      "id": "user_id",
      "name": "John Doe",
      "email": "john@example.com"
    }
  },
  "message": "Login successful"
}

---

# 7. Current User

### Endpoint

GET /api/auth/me

### Headers

Authorization:

Bearer <JWT_TOKEN>

### Response

{
  "success": true,
  "data": {
    "id": "user_id",
    "name": "John Doe",
    "email": "john@example.com"
  }
}

---

# 8. Chat

## Send Message

### Endpoint

POST /api/chat/message

### Headers

Authorization:

Bearer <JWT_TOKEN>

### Request

{
  "conversation_id": "conversation_id",
  "message": "Create an Instagram campaign for my product"
}

For a new conversation:

{
  "conversation_id": null,
  "message": "Create an Instagram campaign for my product"
}

### Response

{
  "success": true,
  "data": {
    "conversation_id": "conversation_id",
    "message_id": "message_id",
    "response": "I will create a marketing campaign...",
    "mode": "GENERAL",
    "status": "COMPLETED"
  },
  "message": null
}

---

# 9. Chat Intent

The backend may internally classify requests as:

GENERAL

or

EXPLICIT_AGENT

Example:

{
  "mode": "GENERAL"
}

or:

{
  "mode": "EXPLICIT_AGENT",
  "agent": "seo"
}

Intent detection is a backend responsibility.

The frontend may display the detected mode but must not independently decide which agent executes.

---

# 10. Explicit Agent Request

The frontend may send an explicitly selected agent.

### Request

POST /api/chat/agent

{
  "agent": "seo",
  "message": "Analyze my website SEO",
  "conversation_id": "conversation_id"
}

Possible backend outcomes:

VALID

INVALID

NEEDS_CLARIFICATION

Example VALID response:

{
  "success": true,
  "data": {
    "agent": "seo",
    "guardrail": "VALID",
    "status": "EXECUTING"
  },
  "message": null
}

Example INVALID:

{
  "success": false,
  "data": {
    "agent": "seo",
    "guardrail": "INVALID"
  },
  "message": "This request is not appropriate for the SEO Agent."
}

Example NEEDS_CLARIFICATION:

{
  "success": true,
  "data": {
    "agent": "seo",
    "guardrail": "NEEDS_CLARIFICATION",
    "question": "Please provide your website URL."
  },
  "message": null
}

---

# 11. Conversation History

## List Conversations

### Endpoint

GET /api/conversations

### Response

{
  "success": true,
  "data": [
    {
      "id": "conversation_1",
      "title": "Instagram Campaign",
      "created_at": "2026-09-23T10:00:00Z",
      "updated_at": "2026-09-23T10:20:00Z"
    }
  ]
}

---

# 12. Get Conversation

### Endpoint

GET /api/conversations/{conversation_id}

### Response

{
  "success": true,
  "data": {
    "id": "conversation_1",
    "title": "Instagram Campaign",
    "messages": [
      {
        "id": "message_1",
        "role": "user",
        "content": "Create an Instagram campaign",
        "created_at": "2026-09-23T10:00:00Z"
      },
      {
        "id": "message_2",
        "role": "assistant",
        "content": "I will create the campaign...",
        "created_at": "2026-09-23T10:01:00Z"
      }
    ]
  }
}

---

# 13. Create Conversation

### Endpoint

POST /api/conversations

### Request

{
  "title": "New Marketing Campaign"
}

### Response

{
  "success": true,
  "data": {
    "id": "conversation_id",
    "title": "New Marketing Campaign"
  }
}

---

# 14. Rename Conversation

### Endpoint

PATCH /api/conversations/{conversation_id}

### Request

{
  "title": "Product Launch Campaign"
}

### Response

{
  "success": true,
  "data": {
    "id": "conversation_id",
    "title": "Product Launch Campaign"
  }
}

---

# 15. Delete Conversation

### Endpoint

DELETE /api/conversations/{conversation_id}

### Response

{
  "success": true,
  "data": null,
  "message": "Conversation deleted"
}

---

# 16. Brand Profile

## Get Brand Profile

### Endpoint

GET /api/brand

### Response

{
  "success": true,
  "data": {
    "company_name": "Example Company",
    "industry": "Technology",
    "website": "https://example.com",
    "description": "Example company description",
    "location": "Mumbai",
    "target_audience": {
      "age_range": "18-35",
      "locations": ["India"],
      "interests": [],
      "pain_points": []
    },
    "brand_voice": "Professional",
    "brand_tone": "Friendly",
    "usp": "Example USP",
    "products_services": [],
    "competitors": [],
    "marketing_goals": []
  }
}

---

# 17. Create / Update Brand Profile

### Endpoint

PUT /api/brand

### Request

{
  "company_name": "Example Company",
  "industry": "Technology",
  "website": "https://example.com",
  "description": "Example description",
  "location": "Mumbai",
  "target_audience": {
    "age_range": "18-35",
    "locations": ["India"],
    "interests": [],
    "pain_points": []
  },
  "brand_voice": "Professional",
  "brand_tone": "Friendly",
  "usp": "Example USP",
  "products_services": [],
  "competitors": [],
  "marketing_goals": []
}

### Response

{
  "success": true,
  "data": {
    "id": "brand_profile_id"
  },
  "message": "Brand profile updated"
}

---

# 18. Campaigns

## List Campaigns

### Endpoint

GET /api/campaigns

### Response

{
  "success": true,
  "data": [
    {
      "id": "campaign_1",
      "name": "Product Launch",
      "objective": "Awareness",
      "status": "ACTIVE",
      "created_at": "2026-09-23T10:00:00Z"
    }
  ]
}

---

# 19. Create Campaign

### Endpoint

POST /api/campaigns

### Request

{
  "name": "Product Launch",
  "objective": "Awareness",
  "product": "Product X",
  "audience": "Young professionals",
  "platforms": [
    "Instagram",
    "LinkedIn"
  ],
  "budget": 50000,
  "duration": {
    "start": "2026-10-01",
    "end": "2026-10-30"
  }
}

### Response

{
  "success": true,
  "data": {
    "id": "campaign_id",
    "name": "Product Launch",
    "status": "DRAFT"
  }
}

---

# 20. Get Campaign

### Endpoint

GET /api/campaigns/{campaign_id}

### Response

{
  "success": true,
  "data": {
    "id": "campaign_id",
    "name": "Product Launch",
    "objective": "Awareness",
    "product": "Product X",
    "audience": "Young professionals",
    "platforms": [
      "Instagram",
      "LinkedIn"
    ],
    "budget": 50000,
    "status": "DRAFT",
    "research": null,
    "competitor_analysis": null,
    "seo": null,
    "content": null,
    "creatives": [],
    "calendar": [],
    "analytics": null
  }
}

---

# 21. Run Campaign Workflow

### Endpoint

POST /api/campaigns/{campaign_id}/run

### Request

{
  "instruction": "Create the complete marketing plan"
}

### Response

{
  "success": true,
  "data": {
    "campaign_id": "campaign_id",
    "run_id": "run_id",
    "status": "STARTED"
  }
}

The backend Planner and Orchestrator control which agents execute.

The frontend does NOT control agent execution order.

---

# 22. Workflow Status

### Endpoint

GET /api/campaigns/{campaign_id}/runs/{run_id}

### Response

{
  "success": true,
  "data": {
    "run_id": "run_id",
    "status": "RUNNING",
    "tasks": [
      {
        "id": "research_1",
        "agent": "research",
        "status": "COMPLETED"
      },
      {
        "id": "competitor_1",
        "agent": "competitor",
        "status": "RUNNING"
      },
      {
        "id": "content_1",
        "agent": "content",
        "status": "PENDING"
      }
    ]
  }
}

Possible states:

PENDING

RUNNING

COMPLETED

FAILED

BLOCKED

---

# 23. Agent Run Details

### Endpoint

GET /api/agent-runs/{run_id}

### Response

{
  "success": true,
  "data": {
    "run_id": "run_id",
    "agent": "research",
    "status": "COMPLETED",
    "started_at": "2026-09-23T10:00:00Z",
    "completed_at": "2026-09-23T10:02:00Z",
    "result": {},
    "confidence": 0.92,
    "error": null
  }
}

---

# 24. Knowledge Base

## Upload Document

### Endpoint

POST /api/knowledge/upload

Content-Type:

multipart/form-data

Supported:

- PDF
- DOCX
- TXT

The backend handles:

Upload
→ Extraction
→ Cleaning
→ Chunking
→ Embedding
→ Vector storage

### Response

{
  "success": true,
  "data": {
    "document_id": "document_id",
    "filename": "brand-guidelines.pdf",
    "status": "PROCESSING"
  }
}

---

# 25. List Documents

### Endpoint

GET /api/knowledge/documents

### Response

{
  "success": true,
  "data": [
    {
      "id": "document_id",
      "filename": "brand-guidelines.pdf",
      "type": "PDF",
      "status": "READY",
      "uploaded_at": "2026-09-23T10:00:00Z"
    }
  ]
}

---

# 26. Delete Document

### Endpoint

DELETE /api/knowledge/documents/{document_id}

### Response

{
  "success": true,
  "data": null,
  "message": "Document deleted"
}

---

# 27. Analytics

## Dashboard Summary

### Endpoint

GET /api/analytics/summary

### Response

{
  "success": true,
  "data": {
    "campaigns": 4,
    "traffic": 12500,
    "engagement": 3400,
    "conversions": 210,
    "revenue": 450000,
    "ctr": 2.8,
    "conversion_rate": 1.68,
    "roi": 3.4
  }
}

These metrics should be calculated deterministically where possible.

---

# 28. Analytics Time Series

### Endpoint

GET /api/analytics/timeseries

### Optional Query Parameters

start_date

end_date

campaign_id

platform

Example:

GET /api/analytics/timeseries?campaign_id=campaign_1

### Response

{
  "success": true,
  "data": [
    {
      "date": "2026-09-01",
      "traffic": 1200,
      "engagement": 340,
      "conversions": 18
    },
    {
      "date": "2026-09-02",
      "traffic": 1400,
      "engagement": 390,
      "conversions": 22
    }
  ]
}

---

# 29. Analytics AI Insights

### Endpoint

POST /api/analytics/insights

### Request

{
  "campaign_id": "campaign_id"
}

### Response

{
  "success": true,
  "data": {
    "summary": "Campaign performance improved...",
    "observations": [],
    "recommendations": []
  }
}

Python calculates the metrics.

Analytics Agent interprets the metrics.

---

# 30. Content Calendar

## Get Calendar

### Endpoint

GET /api/campaigns/{campaign_id}/calendar

### Response

{
  "success": true,
  "data": [
    {
      "id": "calendar_item_1",
      "date": "2026-10-01",
      "platform": "Instagram",
      "type": "POST",
      "caption": "Example caption",
      "status": "SCHEDULED"
    }
  ]
}

---

# 31. Add Calendar Item

### Endpoint

POST /api/campaigns/{campaign_id}/calendar

### Request

{
  "date": "2026-10-01",
  "platform": "Instagram",
  "type": "POST",
  "caption": "Example caption",
  "status": "DRAFT"
}

### Response

{
  "success": true,
  "data": {
    "id": "calendar_item_id"
  }
}

---

# 32. Integrations

## List Integrations

### Endpoint

GET /api/integrations

### Response

{
  "success": true,
  "data": [
    {
      "provider": "google_analytics",
      "status": "NOT_CONNECTED"
    },
    {
      "provider": "google_search_console",
      "status": "NOT_CONNECTED"
    },
    {
      "provider": "instagram",
      "status": "COMING_SOON"
    }
  ]
}

---

# 33. Integration Connection

### Endpoint

POST /api/integrations/{provider}/connect

The backend initiates the appropriate official OAuth/API flow where implemented.

The frontend must never collect third-party passwords.

---

# 34. Agent Names

Canonical agent names:

research

competitor

seo

content

image

analytics

Do not create alternate names such as:

research_agent

ResearchAgent

competitor_analysis_agent

unless explicitly required internally.

The public API should use the canonical names above.

---

# 35. Error Status Codes

Expected HTTP status codes:

200
Successful request

201
Resource created

400
Invalid request

401
Authentication required

403
Permission denied

404
Resource not found

409
Conflict

422
Validation error

500
Internal server error

502
External service failure

---

# 36. Authentication Header

Protected endpoints use:

Authorization: Bearer <JWT_TOKEN>

Frontend should store authentication securely according to the selected authentication strategy.

Never place secrets inside source code.

---

# 37. Frontend Mocking

While backend development is incomplete, the frontend may use mock data matching this API contract.

Mock responses MUST follow the same response structures defined here.

When the backend becomes available, the frontend should replace the mock implementation with real API calls.

The UI should not need to be rewritten simply because mock data is replaced by real data.

---

# 38. API Change Policy

Before changing an API:

1. Update API_CONTRACT.md.
2. Inform affected team members.
3. Update backend.
4. Update frontend.
5. Test both sides.

Avoid breaking changes during active development.

---

# 39. API Security Rules

Never expose:

- LLM API keys
- MongoDB credentials
- JWT secret
- OAuth client secrets
- Third-party access tokens

These remain backend-only.

---

# 40. API Design Principle

The API layer should remain thin.

Preferred flow:

HTTP Request
    ↓
Route
    ↓
Service
    ↓
Planner / Orchestrator / Agent / Database
    ↓
Response Schema
    ↓
HTTP Response

Do NOT put complex business logic directly inside route handlers.

---

# 41. Final Principle

Frontend decides:

"What should be displayed?"

Backend decides:

"What should happen?"

Planner decides:

"What work is required?"

Guardrail decides:

"Is this selected agent appropriate?"

Orchestrator decides:

"How and when should the validated tasks execute?"

Agents decide:

"How should their specialized task be performed?"

Python remains the final execution controller.