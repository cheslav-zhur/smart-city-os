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

The human is CTO / team lead. They name the plan unit. The parent chat **dispatches** specialists; it does not start U+1 or swarm unasked.

Project subagents (`.cursor/agents/`):

- `architect` — ADR/scope briefing; no feature code
- `senior-backend` — U1–U4, U6 API, API side of U7
- `senior-frontend` — U5 console, web side of U7
- `senior-qa` — named tests after a unit; no extra product

**Dispatch** (only after the CTO names a unit, e.g. «делаем U3»):

1. Invoke `architect`. Stop and wait if it reports **wait**, a contradiction, or open choices that need a call (packages, schema, copy, thresholds).
2. Invoke **one** implementer: `senior-backend` or `senior-frontend` for that unit. Never both in parallel. U7: API/postgres first, then web.
3. Invoke `senior-qa` on the finished unit.
4. Stop. The CTO accepts the unit. Do not start the next one.

Do not invoke these roles because a file is open, a test failed in passing, or “it would be good to review.” No proactive swarm.

## How we work

- Build the current plan **one unit at a time** (`docs/plans/01-mvp.md`: U1 → U7). Finish a unit (code + named tests + check) before starting the next.
- **Talk to the user** at unit boundaries: what this unit does, what you are about to write, what you need confirmed (package install, schema shape, copy). Do not silently batch the whole plan.
- If a choice is still open in the plan (thresholds, copy, drone table vs columns), ask instead of inventing a durable default.
- If you see a **contradiction** (scope vs plan, two ADRs, ADR vs code, user request vs a locked decision), **stop**. Name both sides; do not paper over or pick silently.
- **Teach.** The user is learning the system themselves. When a term or a hard step shows up (ingest, collapse, migration, idempotency, a type quirk), explain it in plain language before or with the work. Do not assume jargon is obvious.
- **Commit messages** name the plan unit and the zone, then the why: `feat(api): U5 list cases and events for console poll`. Zones: `api`, `web`, `sim`, `docs`. Do not commit unless the CTO asks.

## While building

- **Tests** ([ADR 0006](docs/adr/0006-tests-without-tdd-on-mvp.md)): ship the tests named in the current plan unit. TDD (red-first) is not required on MVP; consider it from v1 on the API loop only.
- Prefer a modular monolith (folders that could become services later).
- Ingest is idempotent on `event_id`.
- Keep the console a case list + card + two buttons until v1 says otherwise.
