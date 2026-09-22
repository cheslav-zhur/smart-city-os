# Thin wrappers over the documented commands. One Python venv: apps/api/.venv.
# Prefer explicit paths — do not rely on `activate`.

export DATABASE_URL ?= postgresql://city:city@postgres:5432/city
export AUDIT_ACTOR ?= demo-operator

.PHONY: migrate api web sim worker demo stop test-api openapi health-report

migrate:
	cd apps/api && .venv/bin/alembic upgrade head

api:
	cd apps/api && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

web:
	cd apps/web && pnpm dev

sim:
	python apps/sim/run.py

worker:
	cd apps/api && .venv/bin/python -m app.worker

# One terminal: migrate, start api/web/worker, wait for /health, start live sim.
# Desk stays up until make stop. Logs: .local/demo/*.log
demo:
	bash scripts/run-demo.sh

stop:
	bash scripts/stop-demo.sh

test-api:
	cd apps/api && .venv/bin/pytest

openapi:
	cd apps/api && .venv/bin/python scripts/dump_openapi.py
	cd apps/web && pnpm gen:api

# Snapshot pytest + vitest + tsc into .local/health/ (gitignored). Not the duty console.
health-report:
	PYTHONPATH=apps python3 -m health
