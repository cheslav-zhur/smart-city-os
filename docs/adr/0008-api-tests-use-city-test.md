# 0008. API tests use database `city_test`

- Status: Accepted
- Date: 2026-09-21

## Context

The desk, worker, and pytest all read `DATABASE_URL` (`city` in Compose). Pytest truncates domain tables before each `client` test, and the schema test runs Alembic downgrade on the same connection. That wiped the console tape.

## Decision

Keep the desk on `city` ([0004](0004-dev-environment.md)). API pytest rewrites that URL to `city_test` on the same Postgres, creates the database if needed, and migrates it (`apps/api/tests/conftest.py`).

## Consequences

Desk rows survive pytest. CI still has one Postgres service; tests create `city_test` there. No second Compose service and no extra test-runner package.
