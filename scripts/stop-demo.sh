#!/usr/bin/env bash
# Stop api / web / worker / sim started by scripts/run-demo.sh (make demo).
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
dir="$root/.local/demo"

stop_one() {
  local name=$1
  local pidfile="$dir/$name.pid"
  if [[ ! -f "$pidfile" ]]; then
    return
  fi
  local pid
  pid="$(cat "$pidfile")"
  if kill -0 "$pid" 2>/dev/null; then
    pkill -P "$pid" 2>/dev/null || true
    kill "$pid" 2>/dev/null || true
    echo "stopped $name (pid $pid)"
  else
    echo "$name already stopped"
  fi
  rm -f "$pidfile"
}

stop_one sim
stop_one api
stop_one web
stop_one worker
