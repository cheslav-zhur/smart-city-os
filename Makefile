# Thin wrappers over the documented commands. One Python venv: apps/api/.venv.
# Prefer explicit paths — do not rely on `activate`.

export DATABASE_URL ?= postgresql://city:city@postgres:5432/city
export AUDIT_ACTOR ?= demo-operator

.PHONY: migrate api web sim test-api openapi

migrate:
	cd apps/api && .venv/bin/alembic upgrade head

api:
	cd apps/api && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

web:
	cd apps/web && pnpm dev

sim:
	python apps/sim/run.py

test-api:
	cd apps/api && .venv/bin/pytest

openapi:
	cd apps/api && .venv/bin/python scripts/dump_openapi.py
	cd apps/web && pnpm gen:api
