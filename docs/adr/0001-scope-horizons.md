# 0001. Three documentation horizons

- Status: Accepted
- Date: 2026-09-11

## Context

The system can be described as a tiny loop, as a first real product shape, or as a large city platform. Mixing those in one spec either blocks starting or pretends the platform is already the plan.

## Decision

Keep three English docs under `docs/scope/`:

- `01-mvp.md` — smallest runnable loop
- `02-v1.md` — first real shape, still one repo; some items stay open
- `03-north-star.md` — high-load platform picture, not a sprint

Build in that order. Do not implement the north star as a bundle.

## Consequences

New features must name a horizon. “Would be cool on the map” is north-star unless v1 already accepted it. Personal career notes stay out of these files.
