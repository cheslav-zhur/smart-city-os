from __future__ import annotations

import io
import json
from unittest.mock import MagicMock, patch

import pytest
import urllib.error

from run import post_samples
from tape import KIND_CRASH_DROP, Sample


def _http_error(code: int, body: str = "unavailable") -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        url="http://127.0.0.1:8000/events",
        code=code,
        msg="error",
        hdrs=None,
        fp=io.BytesIO(body.encode()),
    )


def _ok_response(payload: dict) -> MagicMock:
    response = MagicMock()
    response.read.return_value = json.dumps(payload).encode()
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


ONE_SAMPLE: list[Sample] = [(0, 45.0, KIND_CRASH_DROP)]


def test_live_post_retries_after_http_error() -> None:
    sleeps: list[float] = []
    responses = [
        _http_error(503),
        _ok_response({"event_id": "e1", "case_id": 7}),
    ]

    with patch("urllib.request.urlopen", side_effect=responses) as urlopen:
        case_id = post_samples(
            "http://127.0.0.1:8000",
            ONE_SAMPLE,
            retry=True,
            sleep=sleeps.append,
        )

    assert case_id == 7
    assert urlopen.call_count == 2
    assert sleeps == [2.0]


def test_live_post_retries_after_url_error() -> None:
    sleeps: list[float] = []
    responses = [
        urllib.error.URLError("connection refused"),
        _ok_response({"event_id": "e1", "case_id": None}),
    ]

    with patch("urllib.request.urlopen", side_effect=responses) as urlopen:
        case_id = post_samples(
            "http://127.0.0.1:8000",
            ONE_SAMPLE,
            retry=True,
            sleep=sleeps.append,
        )

    assert case_id is None
    assert urlopen.call_count == 2
    assert sleeps == [2.0]


def test_tape_post_exits_on_http_error() -> None:
    with patch("urllib.request.urlopen", side_effect=_http_error(500, "boom")):
        with pytest.raises(SystemExit, match="POST /events failed: 500"):
            post_samples(
                "http://127.0.0.1:8000",
                ONE_SAMPLE,
                retry=False,
                sleep=lambda _seconds: None,
            )
