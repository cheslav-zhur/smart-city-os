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

How to run locally: [`docs/dev.md`](docs/dev.md).

## Status

MVP plan: U1–U7 done. Progress lives in [`docs/plans/01-mvp.md`](docs/plans/01-mvp.md) — do not duplicate the table here.

[GitHub Issues](https://github.com/happylolonly/smart-city-os/issues) are an index of large tasks and named units. The current cut is [#1](https://github.com/happylolonly/smart-city-os/issues/1); which units already have a ticket is in the plan’s Issues table. The contract and status stay in [`docs/`](docs/README.md) and that plan. An issue is a pointer, not a second spec.

## Docs

- [docs/README.md](docs/README.md)
- [docs/scope/](docs/scope/README.md)
- [docs/dev.md](docs/dev.md)
