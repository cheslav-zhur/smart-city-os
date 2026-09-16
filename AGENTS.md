# Agent notes

## Language

- Reply to the user in **Russian**.
- Write **code, comments, commit messages, and repo docs in English**.

## What this repo is

**Smart City OS** — operations desk: events → case → proposal → human yes/no → audit. Domain is smart city / urban ops. Do not implement the north-star platform just to match the name.

Read [`docs/scope/`](docs/scope/README.md) before expanding scope.
Read [`docs/adr/`](docs/adr/README.md) before reversing a locked choice.

- [01-mvp.md](docs/scope/01-mvp.md) — build this first
- [02-v1.md](docs/scope/02-v1.md) — grow the same objects; several items still open
- [03-north-star.md](docs/scope/03-north-star.md) — picture only; do not implement as a bundle

Not a chat product. Not a toy map city.

## Hard rules

- The model must not fly a drone or close a road. Tools are an allowlist. Flight is application code after human confirm.
- A code rule must still open a case with no LLM key.
- Do not add Kafka, extra domains, a command-center map, or microservices unless the current horizon doc says so.
- Committed docs describe the **system**, not job-search or interview framing.

## Decisions

When a durable scope or tech choice is locked, add the next `docs/adr/NNNN-*.md` and a row in `docs/adr/README.md`. Do not edit an Accepted ADR to say the opposite — add a new one and mark the old `Superseded by NNNN`. Skip ADRs for still-open questions and for cosmetic taste. English only.

## Agent roster

The human is CTO / team lead. They name the plan unit. The parent chat **does the unit itself**. Optional specialists live in `.cursor/agents/` — invoke only if the CTO names the role (e.g. «позови QA», `@senior-qa`). Do not start U+1 or swarm unasked.

- `architect` — ADR/scope briefing; no feature code
- `senior-backend` — API, schema, simulator, HITL
- `senior-frontend` — console
- `senior-qa` — named tests after a unit; no extra product

Do not invoke these roles because a file is open, a test failed in passing, or “it would be good to review.” No proactive swarm.

## How we work

- Build the current plan **one unit at a time**. Finish a unit (code + named tests + check) before starting the next. After the CTO accepts a unit, mark its **Status** in that plan. Do not mark `done` unasked.
- **GitHub Issues** are an index, not the contract. Scope, ADRs, and the plan stay the source of truth and the status. Open one issue for a large task (a plan cut). Open a unit issue only when the CTO names that unit. The issue body is a link to the plan, not a copy of the spec. An open issue does not authorize starting work.
- **Before starting a unit:** if that unit has no GitHub issue, say so and wait. Do not open one unasked. This cut: V1-U1–V1-U5 are sub-issues of #1; V1-U6 and V1-U7 are not on GitHub yet (see the plan’s Issues index). MVP units stay `U1`–`U7` in `docs/plans/01-mvp.md`.
- **After the CTO accepts a unit:** mark **Status** in the plan first, then push. The unit commit must end with `Closes #n`. GitHub closes that issue only when the commit reaches `main`, not on a local commit. Do not push before acceptance. Do not `gh issue close` unless they ask; the keyword is the close path.
- **Talk to the user** at unit boundaries: what this unit does, what you are about to write, what you need confirmed (package install, schema shape, copy). Do not silently batch the whole plan.
- If a choice is still open in the plan (thresholds, copy, drone table vs columns), ask instead of inventing a durable default.
- Console HTTP types/hooks come from FastAPI OpenAPI via **orval** ([ADR 0007](docs/adr/0007-console-openapi-client.md)). Do not hand-copy paths into `apps/web` or add a second generator. After an API schema change: dump OpenAPI → `pnpm gen:api` → commit dump + generated output.
- If you see a **contradiction** (scope vs plan, two ADRs, ADR vs code, user request vs a locked decision), **stop**. Name both sides; do not paper over or pick silently.
- **Teach.** The user is learning the system themselves. When a term or a hard step shows up (ingest, collapse, migration, idempotency, a type quirk), explain it in plain language before or with the work. Do not assume jargon is obvious.
- **Commit messages** name the plan unit and the zone, then the why: `feat(api): V1-U1 persist kinds, jobs, and opinion columns`. This cut uses `V1-U1`–`V1-U7`; do not reuse bare `U1`–`U7` (those are the done MVP units). Zones: `api`, `web`, `sim`, `docs`, `dev` (Compose, Makefile, `.devcontainer`, run-path glue — not product code). Do not commit unless the CTO asks.
- When a specialist (or you) hits an **environment failure** (disk full / ENOSPC, missing cache, port in use, Postgres down), put it in the parent summary in plain language. Do not hide it behind “tests passed” or treat it as noise. Say what broke, the workaround, and whether the next clone still needs it.

## While building

- **Tests** ([ADR 0006](docs/adr/0006-tests-without-tdd-on-mvp.md)): ship the tests named in the current plan unit. TDD (red-first) is not required on MVP; consider it from v1 on the API loop only.
- Prefer a modular monolith (folders that could become services later).
- Ingest is idempotent on `event_id`.
- Keep the console a case list + card + two buttons until v1 says otherwise.
