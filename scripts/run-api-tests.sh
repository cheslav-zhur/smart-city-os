#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root/apps/api"

if [[ ! -x .venv/bin/pytest || ! -x .venv/bin/alembic ]]; then
  echo "apps/api/.venv is missing or incomplete." >&2
  echo "From apps/api: python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'" >&2
  exit 1
fi

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL is unset. Use the compose/devcontainer workspace." >&2
  exit 1
fi

.venv/bin/alembic upgrade head
.venv/bin/pytest
