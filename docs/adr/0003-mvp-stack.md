# 0003. MVP stack

- Status: Accepted
- Date: 2026-09-11

## Context

The north star is polyglot and many services. The MVP must stay one process to the operator: API, console, simulator, one database. Python is the language for the API and later agent graph. The console should match v1 (React), not a throwaway HTML page.

## Decision

- API: Python, FastAPI
- Data: PostgreSQL (events, cases, audit)
- Console: Vite + React, **pnpm**
- Layout: `apps/api`, `apps/web`, `apps/sim`
- LLM: one gateway later; optional. No key required to run the loop
- No Redis, Kafka, microservices, vector DB, or SSO in MVP

## Consequences

LangGraph and a work queue arrive with v1, not as empty scaffolding. A separate vector store is not the RAG default; files, then pgvector in the same Postgres if needed.
