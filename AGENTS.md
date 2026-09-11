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

## How we work

- Build the current plan **one unit at a time** (`docs/plans/01-mvp.md`: U1 → U7). Finish a unit (code + named tests + check) before starting the next.
- **Talk to the user** at unit boundaries: what this unit does, what you are about to write, what you need confirmed (package install, schema shape, copy). Do not silently batch the whole plan.
- If a choice is still open in the plan (thresholds, copy, drone table vs columns), ask instead of inventing a durable default.

## While building

- **Tests** ([ADR 0006](docs/adr/0006-tests-without-tdd-on-mvp.md)): ship the tests named in the current plan unit. TDD (red-first) is not required on MVP; consider it from v1 on the API loop only.
- Prefer a modular monolith (folders that could become services later).
- Ingest is idempotent on `event_id`.
- Keep the console a case list + card + two buttons until v1 says otherwise.
