#!/usr/bin/env bash
# Start api + web + worker, wait until the API answers, then post the sim tape.
# Processes stay up (logs + pids under .local/demo/). Stop with: make stop
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"

export DATABASE_URL="${DATABASE_URL:-postgresql://city:city@postgres:5432/city}"
export AUDIT_ACTOR="${AUDIT_ACTOR:-demo-operator}"

dir="$root/.local/demo"
venv="$root/apps/api/.venv"
mkdir -p "$dir"

if [[ ! -x "$venv/bin/uvicorn" || ! -x "$venv/bin/alembic" ]]; then
  echo "apps/api/.venv is missing or incomplete." >&2
  echo "From apps/api: python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'" >&2
  exit 1
fi

wait_http() {
  local url=$1
  local tries=$2
  python3 - "$url" "$tries" <<'PY'
import sys, time, urllib.error, urllib.request

url, tries = sys.argv[1], int(sys.argv[2])
for _ in range(tries):
    try:
        urllib.request.urlopen(url, timeout=1)
        sys.exit(0)
    except (urllib.error.URLError, TimeoutError, OSError):
        time.sleep(0.5)
sys.exit(1)
PY
}

port_busy() {
  local port=$1
  python3 - "$port" <<'PY'
import socket, sys
port = int(sys.argv[1])
with socket.socket() as sock:
    sock.settimeout(0.3)
    sys.exit(0 if sock.connect_ex(("127.0.0.1", port)) == 0 else 1)
PY
}

alive() {
  local pidfile=$1
  [[ -f "$pidfile" ]] && kill -0 "$(cat "$pidfile")" 2>/dev/null
}

# cwd, name, command...
start_bg() {
  local cwd=$1
  local name=$2
  local pidfile="$dir/$name.pid"
  shift 2
  if alive "$pidfile"; then
    echo "$name already running (pid $(cat "$pidfile"))"
    return
  fi
  (
    cd "$cwd"
    exec "$@"
  ) >"$dir/$name.log" 2>&1 &
  echo $! >"$pidfile"
  echo "started $name (pid $!, log $dir/$name.log)"
}

if port_busy 8000 && ! alive "$dir/api.pid"; then
  echo "port 8000 is already in use, and not from make demo. Stop that process, or use make stop." >&2
  exit 1
fi
if port_busy 5173 && ! alive "$dir/web.pid"; then
  echo "port 5173 is already in use, and not from make demo. Stop that process, or use make stop." >&2
  exit 1
fi

echo "migrate"
(cd "$root/apps/api" && "$venv/bin/alembic" upgrade head)

start_bg "$root/apps/api" api \
  "$venv/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 --reload

start_bg "$root/apps/web" web \
  pnpm dev

start_bg "$root/apps/api" worker \
  "$venv/bin/python" -m app.worker

echo "waiting for API http://127.0.0.1:8000/health"
if ! wait_http "http://127.0.0.1:8000/health" 60; then
  echo "API did not become healthy. Last log:" >&2
  tail -n 40 "$dir/api.log" >&2 || true
  exit 1
fi

echo "waiting for console http://127.0.0.1:5173"
if ! wait_http "http://127.0.0.1:5173" 90; then
  echo "console did not start. Last log:" >&2
  tail -n 40 "$dir/web.log" >&2 || true
  exit 1
fi

echo "sim tape"
python "$root/apps/sim/run.py"

echo
echo "Desk is up. Console: http://localhost:5173"
echo "Logs: $dir/*.log   Stop: make stop"
