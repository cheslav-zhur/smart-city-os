# Smart City OS

[![CI](https://github.com/cheslav-zhur/smart-city-os/actions/workflows/ci.yml/badge.svg)](https://github.com/cheslav-zhur/smart-city-os/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-1C3C3C?style=flat-square&logo=langchain&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=flat-square&logo=react&logoColor=61DAFB)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)

An operations desk for urban traffic: **ingest → case → proposal → human decision → audit**.

A serious slice of govtech — and a way to practice complex backend / AI patterns in one loop. Not a chat demo, not a product launch.

Traffic samples arrive on one segment (crash-drop, speeding, jam). A code rule may open a **case**; the system can propose a **drone look**. An operator approves or rejects; the decision is recorded. Drone flight here is case state only — no vehicle or fleet integration.

![Operations desk — case card with drone proposal and recent speeds](console.png)

## Demo

Setup, then **`make demo`** (migrate → api + worker + web → live sim until **`make stop`**). Details: [`docs/dev.md`](docs/dev.md).

## What this demonstrates

- Idempotent event ingest that does not wait on the model
- Async jobs for dispatcher / critic opinions
- Case state machine; tool allowlist — agent proposes, only the operator changes drone status
- Modular monolith (folders that could become services later)
- Audit as data (operator decisions + model/tool calls), not stdout

## Loop

```mermaid
flowchart LR
  Sim[Simulator] -->|events| API[API]
  API --> DB[(Postgres)]
  API -->|job| Q[jobs]
  W[Worker] -->|claim| Q
  W -->|opinions + model audit| DB
  W -.-> PB[playbooks]
  W -.-> LLM[LLM gateway]
  Web[Console] <-->|list / card / decide| API
  Op[Operator] -->|approve / reject| Web
```

## Stack

Python / FastAPI / LangGraph · React (Vite) · PostgreSQL · Compose.  
Details: [`docs/stack.md`](docs/stack.md). Decisions: [`docs/adr/`](docs/adr/README.md).

## Horizons

Same loop, three depths. Details in [`docs/scope/`](docs/scope/README.md).

| | Doc | Meaning |
|---|-----|---------|
| 01 | [MVP](docs/scope/01-mvp.md) | Smallest thing that runs — **done** |
| 02 | [v1](docs/scope/02-v1.md) | First real shape, still one repo — **current** |
| 03 | [North star](docs/scope/03-north-star.md) | Large high-load platform — orientation, not a sprint |

## Status

MVP (U1–U7) done. First v1 duty desk (V1-U1–V1-U7) done. Current cut: **live shift desk**. Progress: [plan](.compound-engineering/artifacts/plans/2026-09-21-001-feat-live-shift-desk-plan.md). Issues: [cheslav-zhur/smart-city-os](https://github.com/cheslav-zhur/smart-city-os/issues) (pointers; contract stays in `docs/`).

## Not in this cut

Kafka · microservices · multi-domain sensors · digital twin / map · drone fleet · citizen app · PostGIS.

If events/day blow up first: split ingest, move jobs off the Postgres table, keep the HITL write-path thin. Not coded as a bundle upfront.

## Docs

- [docs/README.md](docs/README.md) — map of scope / ADR / plans
- [docs/stack.md](docs/stack.md) — tech inventory
- [docs/dev.md](docs/dev.md) — run locally
- [docs/scope/](docs/scope/README.md) — what we are building
