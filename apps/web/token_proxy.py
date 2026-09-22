#!/usr/bin/env python3
"""Stdlib reverse proxy: attach a Cloud Run ID token, forward to API_UPSTREAM.

Caddy strips /api and proxies here. Browser keeps one origin; api stays
private (no allUsers) and trusts the web service account.
"""

from __future__ import annotations

import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UPSTREAM = os.environ.get("API_UPSTREAM", "").rstrip("/")
PORT = int(os.environ.get("TOKEN_PROXY_PORT", "8090"))
_HOP = {"host", "authorization", "connection", "transfer-encoding", "keep-alive"}


def _id_token(audience: str) -> str:
    req = urllib.request.Request(
        "http://metadata.google.internal/computeMetadata/v1/"
        f"instance/service-accounts/default/identity?audience={audience}",
        headers={"Metadata-Flavor": "Google"},
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.read().decode()


class Handler(BaseHTTPRequestHandler):
    def _proxy(self) -> None:
        if not UPSTREAM:
            self.send_error(502, "API_UPSTREAM unset")
            return
        length = int(self.headers.get("Content-Length", "0") or 0)
        body = self.rfile.read(length) if length else None
        headers = {
            k: v for k, v in self.headers.items() if k.lower() not in _HOP
        }
        headers["Authorization"] = f"Bearer {_id_token(UPSTREAM)}"
        req = urllib.request.Request(
            f"{UPSTREAM}{self.path}",
            data=body,
            headers=headers,
            method=self.command,
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                self.send_response(resp.status)
                for k, v in resp.headers.items():
                    if k.lower() not in _HOP:
                        self.send_header(k, v)
                self.end_headers()
                self.wfile.write(resp.read())
        except urllib.error.HTTPError as err:
            self.send_response(err.code)
            for k, v in err.headers.items():
                if k.lower() not in _HOP:
                    self.send_header(k, v)
            self.end_headers()
            self.wfile.write(err.read())
        except Exception as err:  # noqa: BLE001 — surface upstream blips as 502
            self.send_error(502, str(err))

    def do_GET(self) -> None:  # noqa: N802
        self._proxy()

    def do_POST(self) -> None:  # noqa: N802
        self._proxy()

    def do_PUT(self) -> None:  # noqa: N802
        self._proxy()

    def do_PATCH(self) -> None:  # noqa: N802
        self._proxy()

    def do_DELETE(self) -> None:  # noqa: N802
        self._proxy()

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._proxy()

    def log_message(self, fmt: str, *args: object) -> None:
        return


def main() -> None:
    if not UPSTREAM:
        raise SystemExit("API_UPSTREAM is required for token_proxy")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
