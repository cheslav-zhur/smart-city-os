# North star

A picture of a large, high-load city / GovTech operations platform. **Not a sprint.** It exists so MVP and v1 stay pieces of this shape, not a different toy.

## Picture

1. **Nerves** — traffic, weather, air, cameras, drones, robots, resident reports, neighboring agencies.
2. **Bus** — a broker so facts do not wait and services do not die together.
3. **Memory** — more than one store: hot now, geo, time series, video, cases, search over playbooks.
4. **Brain** — rules + narrow agents + playbooks. They write into a case. Not a chat.
5. **Human** — the duty officer allows the dangerous step (launch, close a lane, tell a resident “we are on the way”).
6. **Hands** — drone, sign, signal, crew. The world changes only after confirm.
7. **Room** — map, layers, sectors, charts, drone view, roles.

## Stack at this scale

| Layer | Typical pieces |
|-------|----------------|
| Edge | MQTT / IoT, cameras, drones, resident app, intersection edge (act locally, send a summary) |
| Intake | API gateway, NATS or Kafka, schema registry, ingest per domain |
| Work | Domain workers; a long-running process engine (e.g. Temporal) for a flight or a crew dispatch |
| Data | Redis; PostGIS; time-series store; Postgres + audit; object store for video; vector store when playbooks and history are huge |
| AI | Model gateway, inference queue, agent runtime, prompt registry, traces, vision on a separate GPU path |
| Services | traffic, environment, citizen, drones, incidents, notify — talk through events |
| Clients | Command center, crew mobile, resident portal |
| Outside | EMS, police, utility — bus, not shared tables |
| Platform | Kubernetes, SSO, secret store, mTLS, OpenTelemetry, more than one environment |

The MVP/v1 Python + LangGraph process can live **inside** an agent worker. The platform is everything around it.

## AI at this scale

Several specialists, one case card, one human commander.

Roles that show up in a real desk: traffic, resident intake, drone vision, critic, action dispatcher, analyst on demand.

The router is usually code. Autonomy is allowed for **watching** (queue cases overnight), never for hands. Launch and road-close stay human.

A company-wide “AI platform” (many teams, one factory) is outside this repo’s story.

## Backend patterns (where they live)

| Pattern | Why it appears here |
|---------|---------------------|
| Event bus | Many sensors, isolated services |
| Backpressure | Models and UI must not stall ingest |
| CQRS / projections | The desk reads a city picture, not a raw topic |
| Event log / replay | Walk yesterday’s crash |
| Saga / Temporal | Allowed → airborne → frame → hardware fail |
| Outbox | A commit and an emitted event stay together |
| Polyglot persistence | One kind of load ≠ one database |
| Edge | The light acts; the center sees the summary |
| Policy / RBAC | An agent has no `fly` or `close-road` |
| Observability | One id from sensor to the operator’s click |

## How this relates

- [01-mvp.md](01-mvp.md) — one nerve, one process, one database. Same meaning, almost no platform.
- [02-v1.md](02-v1.md) — same meaning, thicker brain and backend in a monolith. Scale questions point here.

Do not implement this document as a bundle so the project “looks large.” Use it to choose the next cut and to explain what would change under load.
