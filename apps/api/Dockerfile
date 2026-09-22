# syntax=docker/dockerfile:1
# Hosted FastAPI. Local desk stays Compose / make demo (`docs/dev.md`).

FROM python:3.12-slim-bookworm

WORKDIR /app

COPY apps/api/pyproject.toml apps/api/alembic.ini ./
COPY apps/api/app ./app
COPY apps/api/alembic ./alembic
COPY apps/api/playbooks ./playbooks

RUN pip install --no-cache-dir .

ENV PORT=8080
EXPOSE 8080

# Cloud Run sets PORT. Alembic uses the same image (`alembic upgrade head`).
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
