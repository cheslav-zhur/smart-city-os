"""Post the canned speed tape to the API. Does not write to the database itself."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tape import TAPE

DEFAULT_API_URL = "http://127.0.0.1:8000"


def post_event(api_url: str, payload: dict) -> dict:
    request = urllib.request.Request(
        f"{api_url.rstrip('/')}/events",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        raise SystemExit(f"POST /events failed: {exc.code} {body}") from exc


def run(api_url: str) -> None:
    run_id = uuid4().hex[:8]
    started = datetime.now(timezone.utc)
    last_offset = 0
    case_id = None
    for index, (offset_seconds, speed) in enumerate(TAPE):
        wait = offset_seconds - last_offset
        if wait > 0:
            time.sleep(wait)
        last_offset = offset_seconds
        payload = {
            "event_id": f"sim-{run_id}-{index:03d}",
            "segment": "A",
            "speed": speed,
            "recorded_at": (started + timedelta(seconds=offset_seconds)).isoformat(),
        }
        result = post_event(api_url, payload)
        if result.get("case_id") is not None:
            case_id = result["case_id"]
        print(
            f"{payload['event_id']} speed={speed} case_id={result.get('case_id')}",
            flush=True,
        )
    if case_id is None:
        raise SystemExit("tape finished but the API did not open a case")
    print(f"opened case {case_id}", flush=True)


def main() -> None:
    api_url = os.environ.get("CITY_API_URL", DEFAULT_API_URL)
    run(api_url)


if __name__ == "__main__":
    main()
