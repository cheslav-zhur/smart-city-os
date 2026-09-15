# Web console layout

Feature-first folders so the desk can grow toward DDD without a premature hexagonal split.

## Tree

```text
src/
  app/                 # shell: compose features, no domain rules
  features/
    cases/             # case list/card, HITL decide, case/drone status
  shared/
    theme/             # light/dark
    lib/               # pure helpers (time, …)
  api/                 # orval client + mutator (infrastructure)
  main.tsx
  index.css
```

## Rules

- Single-file module stays flat (`CaseList.tsx`, `StatusChip.tsx`).
- If a module has more than one file (e.g. component + test), use a folder:
  `CaseCard/CaseCard.tsx` + `CaseCard/CaseCard.test.tsx` (or `time.ts` + `time.test.ts` in the same lib folder).
- Domain string unions for cases live in `features/cases/` (`domain.ts`, `decide.ts`), not in `shared`.
- Do not import `features/*` from `shared/*`.
- Do not hand-edit `api/generated/` — run `make openapi` / `pnpm gen:api` after API schema changes ([ADR 0007](../../docs/adr/0007-console-openapi-client.md)).
- Keep the console as list + card + two buttons until scope says otherwise (`AGENTS.md` / MVP).

## Later (DDD inside a feature)

When a feature gains real application logic, split inside it:

```text
features/cases/
  domain/
  application/   # hooks / use-cases
  ui/            # CaseCard, CaseList, …
```

Do not introduce that split while files are still thin.
