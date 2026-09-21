# Development

How to run the desk locally. Why Compose plus a container: [ADR 0004](adr/0004-dev-environment.md).

Reopen the folder in a container (Cursor: **Dev Containers: Reopen in Container**). Compose starts Postgres 16 and a workspace with Python 3.12 and Node 24. `gh` comes from the Dev Containers `github-cli` feature and uses host `GH_TOKEN`.

`DATABASE_URL` is `postgresql://city:city@postgres:5432/city` (the desk). API pytest uses `city_test` on the same Postgres ([ADR 0008](adr/0008-api-tests-use-city-test.md)). Copy `.env.example` to `.env` at the **repo root** when you add a model key (`LLM_API_KEY`, optional `LLM_BASE_URL` / `LLM_MODEL`). Optional `LOG_LEVEL` (default `INFO`) for worker ops logs via structlog — not the product audit trail. API and worker Settings load that file (process env still overrides). The **worker** fills opinions from the key; the API does not. The desk must still run with no key (empty opinions, approve/reject still work).

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
| Simulator (canned tape once) | `make sim` |
| Worker (opinions) | `make worker` |
| Whole desk + live stream | `make demo` |
| Stop `make demo` processes | `make stop` |
| API tests | `make test-api` |
| Regen console API client | `make openapi` |
| Engineering health snapshot | `make health-report` |

Open the console at the forwarded port **5173**. Daily: `make api`, `make web`, and `make worker` in three terminals, then `python apps/sim/run.py --live` for a shift (or `make sim` for the canned tape once). Or one terminal: **`make demo`** (migrate → start the three → wait → live sim). `make stop` kills api, web, worker, and the live sim. Do not also start the Compose `api`/`web`/`worker` services on the same ports. The worker can run with no `LLM_API_KEY` (empty opinions, approve/reject still work).

`make health-report` writes a **snapshot** under `.local/health/` (gitignored). Spec: [`engineering-health.md`](engineering-health.md). Open `index.html` in a browser. Not live desk state, not an operator screen.

API and sim tests also run on `git push` via [pre-commit](https://pre-commit.com/) (`pre-push` hook, Postgres required), and on GitHub Actions (`.github/workflows/ci.yml`) for `main` and pull requests. No live LLM in CI. Web vitest is not in CI yet; the health page marks that check as **missing**.

## Demo path (Compose profile)

After first-time setup (venv + `pnpm install`), from the repo root inside `dev`:

```bash
make demo
```

That migrates, starts api / web / worker, waits for `/health`, then starts the live sim in the background. Console: http://localhost:5173. Unique incidents keep arriving until **`make stop`**, which kills the sim as well as the three services. `make sim` stays the one-shot mixed tape.

Compose profile (host, not together with `make api` / `make web` on the same ports):

```bash
docker compose --profile demo up postgres api worker web
make sim
```

`make sim` here is still the canned tape fixture, not the live loop. For a live shift use **`make demo`** (or `python apps/sim/run.py --live` against an already running API).

Open http://localhost:5173 → case card (two opinion slots + audit) → approve or reject → an operator row appears in audit on the card.

`api` / `web` / `worker` reuse the same image as `dev` (no second Python toolchain). They are for the demo path only; daily work stays in `dev` + Makefile. The worker claims jobs from Postgres; ingest never waits on the model.
