# Docs

| Folder / file | Role |
|---------------|------|
| [`scope/`](scope/README.md) | What we are building (MVP, v1, north-star) |
| [`stack.md`](stack.md) | What tech is in the repo (inventory; not decisions) |
| [`engineering-health.md`](engineering-health.md) | Dev snapshot of tests / typecheck (not the duty console) |
| [`adr/`](adr/README.md) | Why we chose something (append-only; supersede, do not rewrite) |
| [`plans/01-mvp.md`](plans/01-mvp.md) | MVP units (U1–U7) — done |
| [v1 duty desk plan](../.compound-engineering/artifacts/plans/2026-09-16-001-feat-v1-duty-desk-cut-plan.md) | Active cut (V1-U1–V1-U7); status lives there |
| [`dev.md`](dev.md) | How to run locally (container, venv, `make`, demo path) |
| [`deploy-gcp.md`](deploy-gcp.md) | Hosted live shift on GCP — prod [console](https://web-llohwfu5ga-as.a.run.app) (`main` → `web`/`api`/`worker`/`sim`) |

Chat is not the record. Lock a choice → ADR. Change the product shape → scope. List current tech → `stack.md`. Sequence the build → plan. How to run → `dev.md`. How the hosted desk is deployed → `deploy-gcp.md`. Local test snapshot → `engineering-health.md`.
