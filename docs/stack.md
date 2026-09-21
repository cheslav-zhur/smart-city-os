# Stack

What is in the repo today. **Why** a choice landed → [`adr/`](adr/README.md) (do not duplicate decisions here). How to run → [`dev.md`](dev.md).

Layout: `apps/api` · `apps/web` · `apps/sim` · `apps/health` (engineering snapshot, not the desk).

## API / worker

| Piece | Choice |
|-------|--------|
| Language | Python 3.12 |
| HTTP | FastAPI + Uvicorn |
| ORM / migrations | SQLAlchemy + Alembic |
| DB driver | psycopg |
| Settings | pydantic-settings |
| Job queue | Postgres job table (same DB); worker in `app.worker` |
| Ops logs | structlog (not the product audit trail) |

Ingest stays on the API path and does not wait on the model. The worker claims jobs and fills opinions asynchronously.

## AI

| Piece | Choice |
|-------|--------|
| Graph | LangGraph — dispatcher → critic (`StateGraph`) |
| Tools | langchain tools + allowlist; drone status only after human confirm in app code |
| Chat model | one LLM gateway via `langchain-openai` (`ChatOpenAI`-compatible); key optional |
| Playbooks | markdown files the graph can search |
| Without a key | desk still runs — empty opinions, approve/reject + audit work |

Proposal ≠ execute. Model/tool calls land in audit as data.

## Data

| Piece | Choice |
|-------|--------|
| Store | PostgreSQL 16 |
| Domain tables | events, cases, jobs, audit (and related) |
| Vector search | not default; files first, `pgvector` in the same Postgres only if needed later |

## Console

| Piece | Choice |
|-------|--------|
| UI | React 19 + TypeScript |
| Bundler | Vite |
| Package manager | pnpm |
| Data fetching | TanStack Query |
| API client | orval from FastAPI OpenAPI → generated React Query hooks ([ADR 0007](adr/0007-console-openapi-client.md)) |
| Styles | Tailwind CSS v4 |
| Shape | list / case card / decide — not a map, not a chat |

## Ops / quality

| Piece | Choice |
|-------|--------|
| Local | Dev Container + Docker Compose (`postgres`, `dev`; demo profile for `api`/`web`) |
| Simulator | stdlib script (`make sim`) — not IoT |
| API tests | pytest (+ httpx) against Postgres `city_test` ([ADR 0008](adr/0008-api-tests-use-city-test.md)); CI on `main` / PRs |
| Console tests | vitest locally; not in CI until the console thickens |
| Engineering health | [`engineering-health.md`](engineering-health.md) — `apps/health` snapshot; not the duty console |

## Explicitly not here

Redis · Kafka · microservices · separate vector DB · SSO · PostGIS · drone fleet SDK · citizen app.

If something above changes as a decision, write or supersede an ADR — then refresh this page to match.
