#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
api_venv="$root/apps/api/.venv"

if [[ ! -x "$api_venv/bin/pytest" || ! -x "$api_venv/bin/alembic" ]]; then
  echo "apps/api/.venv is missing or incomplete." >&2
  echo "From apps/api: python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'" >&2
  exit 1
fi

(cd "$root/apps/sim" && "$api_venv/bin/pytest")

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL is unset. Use the compose/devcontainer workspace." >&2
  exit 1
fi

cd "$root/apps/api"
"$api_venv/bin/alembic" upgrade head
"$api_venv/bin/pytest"
