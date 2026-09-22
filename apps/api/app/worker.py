"""Worker entry: `python -m app.worker`. Not an HTTP process.

Cloud Run still probes $PORT, so when PORT is set we serve a tiny /health
in a daemon thread while the job loop polls Postgres.
"""

from __future__ import annotations

import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import structlog

from app.jobs.loop import run_worker
from app.logging_setup import configure_logging
from app.settings import get_settings


def _start_health_server(port: int) -> None:
    """Stdlib /health for Cloud Run startup probes. Local make worker leaves PORT unset."""

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


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    log = structlog.get_logger("app.worker")
    port = os.environ.get("PORT")
    if port:
        _start_health_server(int(port))
        log.info("worker_health_listening", port=int(port))
    log.info(
        "worker_starting",
        log_level=settings.log_level.upper(),
        llm_configured=bool(settings.llm_api_key),
    )
    run_worker()


if __name__ == "__main__":
    main()
