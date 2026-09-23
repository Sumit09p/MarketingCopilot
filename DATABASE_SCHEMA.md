# MarketingOS AI — Database Schema

## 1. Database

Database:

MongoDB Atlas

Database name:

marketingos

MongoDB is the primary persistent database for application data.

---

# 2. Design Principles

The database must:

- Keep user data isolated.
- Use stable document IDs.
- Avoid unnecessary duplication.
- Store relationships using IDs.
- Keep agent execution traceable.
- Keep campaign data connected to its owner/company.
- Never store passwords in plain text.
- Never store API secrets directly in normal application documents unless securely encrypted and explicitly required.
- Never store LLM API keys in MongoDB.

---

# 3. Collections

The initial collections are:

```text
users
companies
brand_profiles
conversations
messages
campaigns
agent_runs
documents
knowledge_chunks
integrations
analytics