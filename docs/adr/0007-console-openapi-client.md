# 0007. Console OpenAPI client (orval + TanStack Query)

- Status: Accepted
- Date: 2026-09-15
- Extends: [0003](0003-mvp-stack.md)

## Context

The console used a hand-written `api.ts` with local DTOs. That drifts from FastAPI. [02-v1.md](../scope/02-v1.md) left “generate from `/openapi.json`” open; approve/reject now return a named Pydantic model so OpenAPI is not a generic object.

Browser `/api` is a Vite proxy rewrite to FastAPI’s unprefixed routes — not a second API.

## Decision

- Generate the console HTTP client and React Query hooks with **orval** (`client: 'react-query'`) from a committed FastAPI OpenAPI dump (`apps/web/openapi.json`).
- Runtime dependency: **@tanstack/react-query**.
- Commit orval output under `apps/web/src/api/generated/` so `pnpm test` / demo work without a generate step.
- After an API schema change: dump OpenAPI → `pnpm gen:api` → commit dump + generated files with the API change.
- Do not introduce a second generator (openapi-typescript, Axios clients, etc.) without a new ADR.

## Consequences

Hand-written `apps/web/src/api.ts` is retired. Console UX stays list + card + two buttons until scope says otherwise. Regenerating the client is part of API contract work, not every unrelated PR.
