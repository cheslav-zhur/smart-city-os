# Engineering health

A **local snapshot** of test and typecheck status for the whole repo (API, console, sim). Not the duty console. Not `GET /health` (that route only means Postgres answers).

Operators never see this page. It is for people working in the repo.

## Slice 0 (what shipped)

`make health-report` runs the existing tools, writes machine-readable JSON, then fills a static HTML template.

```text
pytest (api) + pytest (sim) + vitest + tsc -b
        ↓
  .local/health/quality.json     (gitignored)
        ↓
  apps/health/template.html  +  JSON
        ↓
  .local/health/index.html       (open in a browser)
```

The HTML does **not** start pytest or vitest. It only shows the last snapshot. If the file is missing, run the make target. If `generated_at` is older than 24 hours, the page shows a stale banner.

| In slice 0 | Out of slice 0 |
|------------|----------------|
| Pass / fail / skip counts | Coverage % (`pytest-cov`, vitest coverage) |
| Hard module map (test file → row) | Import-graph or “who tests this .py” |
| `tsc -b` exit code | ESLint, Ruff, mypy |
| `web_in_ci: missing` (fact from stack) | GitHub Checks as the live source |
| Static HTML from a template | FastAPI `/internal/dev/health`, orval, a route in `App.tsx` |
| Stdlib + tools already in the venv / pnpm tree | New pip/pnpm packages |

`missing` means the gate does not exist. `failed` means the gate exists and broke.

## Package

`apps/health` is a stdlib package. One Python venv remains `apps/api/.venv` (pytest lives there). No second toolchain.

| File | Role |
|------|------|
| `modules.py` | Test filename → dashboard module id |
| `parse.py` | pytest JUnit XML, vitest JSON |
| `collect.py` | Runs the tools, writes `.local/health/` |
| `render.py` | Substitutes `__QUALITY_JSON__` and `__STALE_HOURS__` |
| `template.html` | Page markup (edit here, not in Python) |
| `tests/test_parse.py` | Parser + template contract (no Postgres) |

Run the package tests:

```bash
PYTHONPATH=apps python3 -m unittest health.tests.test_parse
```

How to take a snapshot: [`dev.md`](dev.md) (`make health-report`).

## `quality.json`

`schema_version` is `1`. Bump it if the shape changes.

```json
{
  "schema_version": 1,
  "generated_at": "2026-09-21T03:13:02Z",
  "git": { "sha": "82f72da", "branch": "main", "dirty": true },
  "suites": {
    "api": { "total": 49, "passed": 49, "failed": 0, "skipped": 0, "status": "passed", "duration_s": 69.9 },
    "sim": { "total": 2,  "passed": 2,  "failed": 0, "skipped": 0, "status": "passed", "duration_s": 0.01 },
    "web": { "total": 11, "passed": 11, "failed": 0, "skipped": 0, "status": "passed", "duration_s": 0.12 }
  },
  "checks": {
    "api_pytest": "passed",
    "sim_pytest": "passed",
    "web_vitest": "passed",
    "web_tsc": "passed",
    "web_in_ci": "missing"
  },
  "modules": [
    { "id": "api.events", "layer": "api", "tests": 10, "failed": 0, "status": "passed" }
  ],
  "failures": []
}
```

Suite `status`: `passed` | `failed` | `error` (`error` = the runner did not produce a report, e.g. missing venv).

`failures[]`: `{ suite, nodeid, message }` for red tests only.

Unmapped tests: a new `test_*.py` / `*.test.ts` that is not in `modules.py` still counts in `suites.*.total`. The HTML warns when `sum(modules.tests) != sum(suites.total)`. Add a row in `MODULE_FILES` when that happens on purpose.

## Module map

One test file → one module. Cross-cutting files sit on the row that matches the **console contract**, not every import.

| id | Layer | Files |
|----|--------|--------|
| `api.health` | api | `test_health.py` |
| `api.events` | api | `test_ingest.py`, `test_event_kinds.py` |
| `api.cases` | api | `test_hitl.py`, `test_console_reads.py` |
| `api.jobs` | api | `test_jobs.py` |
| `api.llm` | api | `test_agents.py`, `test_playbook.py`, `test_llm_stub.py`, `test_openai_tool_call_extras.py` |
| `api.schema` | api | `test_schema_v1.py` |
| `web.cases` | web | `CaseCard.test.tsx` |
| `web.shared` | web | `time.test.ts` |
| `sim.tape` | sim | `test_tape.py` |

`test_console_reads.py` is `api.cases` (list + audit on the card). There is no `api.audit` row until a dedicated test file exists. Storybook stories are not tests; `web.shared.ui` is not a row.

Do not confuse `api.health` (pytest for `GET /health`) with this package.

## Later (named, not started)

Each of these needs an explicit ok (new packages, CI shape, or a scope/ADR change). Do not fold them into V1-U7.

1. **Coverage** — `pytest-cov` and vitest coverage → `%` on the module row, then file drill-down. Thresholds become `warning` / `failed`, not `missing`.
2. **Web in CI** — add vitest to `.github/workflows/ci.yml`, then change `web_in_ci` from `missing` to a real pass/fail. Settle Storybook extra deps first (`apps/web/README.md`).
3. **Lint / types on API** — Ruff / mypy as extra checks, same `passed` / `failed` / `missing` vocabulary.
4. **CI as the source of truth** — last GitHub run instead of (or in addition to) the local snapshot. Still a file or artifact, not the duty API.
5. **Internal HTTP** — `GET /internal/dev/health` that **reads the snapshot from disk**, localhost / env-gated. Do not run pytest inside uvicorn. Do not put this on orval or the operator console.
6. **Visual QA** — Storybook stories for `CaseCard` states (separate from this dashboard). Chromatic only after the gallery exists.

Not on this path: a Nest/Next control plane, AI evals / RAG traffic lights, dependency-cruiser, a second screen in `App.tsx`. The console stays list + card + two buttons until scope says otherwise.

## Relation to the desk

Duty loop: events → case → opinions → human yes/no → audit. That product lives in `apps/api` and `apps/web`.

This package watches **whether the tests for that loop are green**. Same repo, different audience.
