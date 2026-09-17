# Development

How to run the desk locally. Why Compose plus a container: [ADR 0004](adr/0004-dev-environment.md).

Reopen the folder in a container (Cursor: **Dev Containers: Reopen in Container**). Compose starts Postgres 16 and a workspace with Python 3.12 and Node 24. `gh` comes from the Dev Containers `github-cli` feature and uses host `GH_TOKEN`.

`DATABASE_URL` is `postgresql://city:city@postgres:5432/city`. Copy `.env.example` to `.env` when you add a model key; the loop must run without one.

Web packages: **pnpm**. Named volumes keep pip / pnpm / uv caches across container rebuilds. Image layers cache apt, Node, and pnpm until the Dockerfile changes.

## First-time setup (inside `dev`)

One Python venv only — `apps/api/.venv`. Prefer explicit `.venv/bin/…` paths (no `activate`). Sim stays stdlib; no second venv.

```bash
cp .env.example .env
cd apps/api && python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'
cd ../web && pnpm install
cd ../..
make migrate
apps/api/.venv/bin/pre-commit install
```

## Daily commands

| Goal | Command |
|------|---------|
| Migrate | `make migrate` |
| API (reload) | `make api` |
| Console | `make web` |
| Simulator | `make sim` |
| API tests | `make test-api` |
| Regen console API client | `make openapi` |

Open the console at the forwarded port **5173**. Run `make api` and `make web` in two terminals inside `dev`. Do not also start the Compose `api`/`web` services on the same ports.

API tests also run on `git push` via [pre-commit](https://pre-commit.com/) (`pre-push` hook, Postgres required).

## Demo path (Compose profile)

After first-time setup (venv + `pnpm install` + migrate), from the repo root:

```bash
docker compose --profile demo up postgres api web
```

In another shell (host or `dev`):

```bash
make sim
```

Open http://localhost:5173 → case card → approve or reject → check an `audit_entries` row (e.g. via `psql` or the API).

`api` / `web` reuse the same image as `dev` (no second Python toolchain). They are for the demo path only; daily work stays in `dev` + Makefile.
