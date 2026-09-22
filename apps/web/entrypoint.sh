#!/bin/sh
# Cloud Run: Caddy on $PORT; optional token proxy for private api.
set -e
if [ -n "${API_UPSTREAM}" ]; then
  python3 /usr/local/bin/token_proxy.py &
fi
exec caddy run --config /etc/caddy/Caddyfile --adapter caddyfile
