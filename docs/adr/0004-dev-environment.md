# 0004. Dev environment

- Status: Accepted
- Date: 2026-09-11

## Context

API (Python) and console (Node) plus Postgres will drift if each laptop installs them ad hoc. `clone → up` should be Compose. Daily work should be the same stack inside a devcontainer.

The official Python image’s Yarn apt repo has a broken GPG key; `apt-get update` must not see it. Yarn’s apt source is removed in the image build.

## Decision

- Root `docker-compose.yml`: `postgres` + `dev` (workspace)
- `.devcontainer` uses that compose file
- Image: Python 3.12, Node 24, pnpm 10 via corepack
- Named volumes: pip, pnpm store, uv — survive container recreate
- `DATABASE_URL=postgresql://city:city@postgres:5432/city`

## Consequences

Rebuild the image when the Dockerfile changes (Node major, pnpm). Do not `docker compose build --no-cache` unless the layer cache is wrong. Host-only Node/Python is not the supported path.
