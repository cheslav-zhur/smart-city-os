# Architecture decision records

Durable **why**, not a diary and not a product spec.

- **Scope** (`docs/scope/`) — what the system is at MVP / v1 / north-star.
- **ADR** (this folder) — a choice we will not silently reverse. Numbered, append-only. To change course, add a new record and mark the old one `Superseded`.
- **Chat** — scratch. If it should survive, it lands in scope or an ADR.

Write ADRs in English. One decision per file. Skip ADRs for taste (button padding) and for things still open.

| ID | Decision | Status |
|----|----------|--------|
| [0001](0001-scope-horizons.md) | Three horizons: MVP, v1, north-star | Accepted |
| [0002](0002-mvp-loop.md) | One road, speed collapse, human-gated drone | Accepted |
| [0003](0003-mvp-stack.md) | Python, FastAPI, Postgres, React, pnpm | Accepted |
| [0004](0004-dev-environment.md) | Compose + devcontainer, Node 24, package caches | Accepted |
| [0005](0005-tdd.md) | Red → green → refactor for feature work | Superseded by 0006 |
| [0006](0006-tests-without-tdd-on-mvp.md) | MVP: tests yes, TDD no; TDD maybe from v1 | Accepted |
| [0007](0007-console-openapi-client.md) | Console HTTP client: orval + TanStack Query from OpenAPI | Accepted |
| [0008](0008-api-tests-use-city-test.md) | API pytest uses Postgres `city_test`, not desk `city` | Accepted |
