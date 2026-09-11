# Smart City OS

An operations desk in the smart-city domain, not a chatbot and not a simulated metropolis. The north star is a full city platform; this repo grows toward that.

Facts come in (at first: speed on one road). The system may open a **case** and propose a **drone look**. A human confirms or rejects. The decision is written down. The drone in this repo is a status, not an aircraft.

## Horizons

Same loop, three depths. Details in [`docs/scope/`](docs/scope/README.md).

| | Doc | Meaning |
|---|-----|---------|
| 01 | [MVP](docs/scope/01-mvp.md) | Smallest thing that runs |
| 02 | [v1](docs/scope/02-v1.md) | First real shape, still one repo |
| 03 | [North star](docs/scope/03-north-star.md) | Large high-load platform — orientation, not a sprint |

Build in that order. Do not implement the north star as a bundle.

## Stack (MVP)

Python, FastAPI, PostgreSQL, one LLM gateway, a thin console, a simulator script. Docker Compose for `up`.

The model may draft a proposal. It has no `fly()`. Application code changes drone status after confirm.

## Development

Reopen the folder in a container (Cursor: **Dev Containers: Reopen in Container**). Compose starts Postgres 16 and a workspace with Python 3.12 and Node 24.

`DATABASE_URL` is `postgresql://city:city@postgres:5432/city`. Copy `.env.example` to `.env` when you add a model key; the loop must run without one.

Web packages: **pnpm**. Named volumes keep pip / pnpm / uv caches across container rebuilds. Image layers cache apt, Node, and pnpm until the Dockerfile changes.

API tests run on `git push` via [pre-commit](https://pre-commit.com/) (`pre-push` hook, Postgres required). After creating the API venv (`cd apps/api && python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'`), from the repo root:

```bash
apps/api/.venv/bin/pre-commit install
```

## Status

Scope docs and the dev container are in place. App runtime is not. Start from the MVP.

## Docs

- [docs/README.md](docs/README.md)
- [docs/scope/](docs/scope/README.md)
