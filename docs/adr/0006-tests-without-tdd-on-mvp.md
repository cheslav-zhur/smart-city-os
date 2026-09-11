# 0006. Tests on MVP, TDD deferred

- Status: Accepted
- Date: 2026-09-11
- Supersedes: [0005](0005-tdd.md)

## Context

Red → green → refactor is a good fit for the API loop later, and a poor fit for learning the domain, Compose, and the first console at the same time. Dogmatic TDD on glue and UI is ceremony. Skipping tests entirely would hide ingest/HITL bugs.

## Decision

**MVP:** write tests as usual (pytest for the API loop; thin UI test where cheap). Order is implementer choice — not required red-first. U7 remains a documented run.

**v1 (open until then):** start TDD on the domain contract (ingest, rules, HITL, agent tools). Still not TDD for Compose, copy, or layout.

Do not ship a unit from the MVP plan without the tests that unit already names, except U7.

## Consequences

0005’s “no production code without a failing test” does not apply to MVP. pytest is still a first-class dependency. Revisiting TDD is a v1 ADR or a note in `docs/scope/02-v1.md`, not a silent return to 0005.
