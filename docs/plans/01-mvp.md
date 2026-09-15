---
title: MVP implementation
date: 2026-09-11
origin: docs/scope/01-mvp.md
adrs:
  - docs/adr/0002-mvp-loop.md
  - docs/adr/0003-mvp-stack.md
  - docs/adr/0004-dev-environment.md
  - docs/adr/0006-tests-without-tdd-on-mvp.md
---

# MVP implementation

Make the duty loop run: live speed tape → collapse → case → yes/no → drone status → audit. No LLM key required.

Origin: [docs/scope/01-mvp.md](../scope/01-mvp.md). Do not implement v1 or north-star items here.

## Problem frame

Scope and ADRs are locked. At plan start there was no API, schema, simulator, or console — only a devcontainer. An implementer needs a sequence of units, file homes, and checks, not another product debate. Current progress is the status table, not this paragraph.

## Scope

In: `apps/api`, `apps/web`, `apps/sim`, Compose services for api + web + postgres, tests for the loop.

Out: map, RAG, job queue, LangGraph, second agent, extra event types, SSO, Kafka.

## Key decisions

| Choice | Call | Why |
|--------|------|-----|
| Poll the API from the console | No websocket | Live tape is ~40s; refresh/poll is enough |
| LLM off the request path if unset | Stub returns no rationale | ADR 0002: rule + button always work |
| Collapse rule | Last two samples: drop to ~0 after a moving speed | Tunable constant; keep it obvious |
| ORM | SQLAlchemy 2 + Alembic | One schema story; migrations from the first table |
| API ↔ web | Vite proxy `/api` → FastAPI | One origin in the browser |

Threshold numbers and copy are execution-time; do not block the plan.

## Execution

**Tests, not TDD** ([ADR 0006](../adr/0006-tests-without-tdd-on-mvp.md)). Each feature unit lists tests — write them in the same unit, order is free. Red-first is not required until v1.

## Units

Do them in order. Each unit should leave tests greener than before. The CTO marks **Status** when they accept a unit. Do not mark `done` unasked. Goal / Files / Tests stay the contract.

| Unit | Status |
|------|--------|
| U1 API skeleton | done |
| U2 ingest / collapse | done |
| U3 HITL | done |
| U4 simulator | done |
| U5 console | done |
| U6 LLM stub | done |
| U7 run path | todo |

### U1 — API skeleton and schema

**Goal.** FastAPI process, Postgres schema, `/health` checks the DB.

**Files.** `apps/api/` (package, settings from `DATABASE_URL`), Alembic under `apps/api/alembic/`, tables: `events`, `cases`, `audit_entries` (drone fields on `cases` or a `drones` row keyed by case).

**Tests.** `apps/api/tests/test_health.py`: `GET /health` is 200 when Postgres is up.

**Check.** Empty tables exist after migrate.

### U2 — Ingest and collapse rule

**Goal.** `POST /events` is idempotent on `event_id`. Speed samples for segment `A`. Rule opens at most one `open` case on collapse.

**Files.** `apps/api/app/events/`, `apps/api/app/cases/`.

**Tests.** `apps/api/tests/test_ingest.py`: duplicate `event_id` → one row; collapse sequence → one case; no collapse → no case.

### U3 — Confirm / reject, drone, audit

**Goal.** `POST /cases/{id}/approve` and `/reject`. Approve sets drone `in_flight` then `on_site` (can be immediate stub steps). Reject keeps `idle`. Both write audit (actor from env, action, time, short why). No `fly()` API for the model.

**Files.** `apps/api/app/drone/`, `apps/api/app/audit/`.

**Tests.** `apps/api/tests/test_hitl.py`: approve → status + audit; reject → idle + audit; unknown case → 404.

### U4 — Simulator

**Goal.** Script posts ~40s of moving speed on `A`, then a collapse. Uses the API only.

**Files.** `apps/sim/`.

**Tests.** `apps/sim/tests/test_tape.py` (or api client test): the canned sequence is a collapse that would open a case.

### U5 — Console

**Goal.** Vite + React + pnpm: case list, card, two buttons, last speeds. Poll for events/cases. Not a chat.

**Files.** `apps/web/`.

**Tests.** Thin React test for the card (buttons call approve/reject). Duty path still covered by U3. Manual: after sim, card → yes/no.

### U6 — Optional rationale

**Goal.** If `LLM_*` env is set, one call may fill “why” on the card. If not, UI still shows the rule proposal. Tools: read recent events, write draft text. No flight tool.

**Files.** `apps/api/app/llm/`.

**Tests.** `apps/api/tests/test_llm_stub.py`: unset key → no crash, case still approvable.

### U7 — Run path

**Goal.** Compose (or a compose override) runs `api`, `web`, `postgres`. README: migrate, `up`, run sim, open the console.

**Files.** `docker-compose.yml` (add services; keep `dev`), `README.md`, `.env.example`.

**Check.** Documented path: up → sim → click → audit row.

**Todo (venv / daily commands).** Document one Python venv only: `apps/api/.venv` (create via README: `python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'`). Prefer explicit `apps/api/.venv/bin/…` for alembic / uvicorn / pytest / pre-commit so shells and agents do not depend on `activate` or a root `/workspace/.venv`. Sim stays stdlib (`python apps/sim/run.py`) — no second venv. Optional thin Makefile wrappers (`migrate`, `api`, `web`, `sim`, `test-api`) over those same commands; do not invent a second Python toolchain (ADR 0004).

## Risks

- Collapse rule too tight/loose — fix the constant, not the architecture.
- Devcontainer vs `api`/`web` images: develop in `dev`; `api`/`web` services are for the demo path. Do not invent a second Python toolchain.
- Putting LangGraph in U1 — out of scope; stub in U6.

## Trace

| Scope / ADR | Units |
|-------------|--------|
| clone → up → sim → card → yes/no → audit | U4, U5, U7 |
| Rule without LLM key | U2, U6 |
| Human-gated drone, no `fly()` | U3 |
| React console | U5 |
| Idempotent ingest | U2 |
