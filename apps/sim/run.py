"""Post traffic samples to the API. Does not write to the database itself.

Local: CITY_API_URL defaults to http://127.0.0.1:8000; no auth header.
Hosted Cloud Run: set CITY_API_ID_TOKEN=1 so each POST carries a Google ID
token (audience = CITY_API_URL) for private api. When PORT is set, serve
/health for Cloud Run probes while --live runs.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent))

from stream import event_id, iter_live_samples
from tape import MIXED_TAPE, Sample

DEFAULT_API_URL = "http://127.0.0.1:8000"
LIVE_RETRY_SLEEP_SECONDS = 2.0


def _cloud_run_id_token(audience: str) -> str:
    """Fetch an ID token from the metadata server (Cloud Run / GCE)."""
    req = urllib.request.Request(
        "http://metadata.google.internal/computeMetadata/v1/"
        f"instance/service-accounts/default/identity?audience={audience}",
        headers={"Metadata-Flavor": "Google"},
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.read().decode()


def _start_health_server(port: int) -> None:
    """Stdlib /health for Cloud Run. Local make sim leaves PORT unset."""

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            path = self.path.split("?", 1)[0]
            if path in ("/health", "/"):
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"ok\n")
                return
            self.send_error(404)

        def log_message(self, fmt: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    threading.Thread(target=server.serve_forever, name="health", daemon=True).start()


def post_event(api_url: str, payload: dict) -> dict:
    base = api_url.rstrip("/")
    headers = {"Content-Type": "application/json"}
    if os.environ.get("CITY_API_ID_TOKEN"):
        headers["Authorization"] = f"Bearer {_cloud_run_id_token(base)}"
    request = urllib.request.Request(
        f"{base}/events",
        data=json.dumps(payload).encode(),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode())


def _post_failure_message(exc: urllib.error.URLError) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        body = exc.read().decode()
        return f"POST /events failed: {exc.code} {body}"
    return f"POST /events failed: {exc}"


def post_samples(
    api_url: str,
    samples: Iterable[Sample],
    *,
    retry: bool = False,
    sleep: Callable[[float], None] = time.sleep,
) -> int | None:
    """Post samples in order. Returns the last opened case id, if any.

    When retry is True (live stream), transient HTTP/URL errors sleep and
    re-post the same sample. The canned tape keeps SystemExit on failure.
    """
    run_id = uuid4().hex[:8]
    started = datetime.now(timezone.utc)
    last_offset = 0
    case_id = None
    for index, (offset_seconds, speed, kind) in enumerate(samples):
        wait = offset_seconds - last_offset
        if wait > 0:
            sleep(wait)
        last_offset = offset_seconds
        payload = {
            "event_id": event_id(run_id, index),
            "segment": "A",
            "speed": speed,
            "kind": kind,
            "recorded_at": (started + timedelta(seconds=offset_seconds)).isoformat(),
        }
        while True:
            try:
                result = post_event(api_url, payload)
                break
            except urllib.error.URLError as exc:
                message = _post_failure_message(exc)
                if not retry:
                    raise SystemExit(message) from exc
                print(
                    f"{message}; retrying in {LIVE_RETRY_SLEEP_SECONDS}s",
                    flush=True,
                )
                sleep(LIVE_RETRY_SLEEP_SECONDS)
        if result.get("case_id") is not None:
            case_id = result["case_id"]
        print(
            f"{payload['event_id']} kind={kind} speed={speed} "
            f"case_id={result.get('case_id')}",
            flush=True,
        )
    return case_id


def run_tape(api_url: str) -> None:
    case_id = post_samples(api_url, MIXED_TAPE)
    if case_id is None:
        raise SystemExit("tape finished but the API did not open a case")
    print(f"opened case {case_id}", flush=True)


def run_live(api_url: str) -> None:
    try:
        post_samples(api_url, iter_live_samples(), retry=True)
    except KeyboardInterrupt:
        print("live stream stopped", flush=True)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Post traffic samples to the city API."
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Post unique incidents until stopped. Default is the canned mixed tape once.",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    port = os.environ.get("PORT")
    if port:
        _start_health_server(int(port))
        print(f"sim_health_listening port={port}", flush=True)
    api_url = os.environ.get("CITY_API_URL", DEFAULT_API_URL)
    if args.live:
        run_live(api_url)
    else:
        run_tape(api_url)


if __name__ == "__main__":
    main()
