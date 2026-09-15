"""U6: optional rationale stub — unset key must not break the duty loop."""

from datetime import UTC, datetime, timedelta

import pytest

from app.models import Case
from app.settings import get_settings


def _event(event_id: str, speed: float, seconds: int = 0) -> dict:
    return {
        "event_id": event_id,
        "segment": "A",
        "speed": speed,
        "recorded_at": (
            datetime(2026, 9, 11, 5, 0, tzinfo=UTC) + timedelta(seconds=seconds)
        ).isoformat(),
    }


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_unset_key_leaves_rationale_null_and_case_approvable(
    client, db_session, monkeypatch
) -> None:
    monkeypatch.delenv("LLM_API_KEY", raising=False)

    client.post("/events", json=_event("llm-move", 40.0))
    opened = client.post("/events", json=_event("llm-stop", 0.0, seconds=5))
    case_id = opened.json()["case_id"]
    assert case_id is not None

    case = db_session.get(Case, case_id)
    assert case is not None
    assert case.rationale is None

    listed = client.get("/cases").json()
    assert listed[0]["rationale"] is None

    approve = client.post(f"/cases/{case_id}/approve")
    assert approve.status_code == 200
    assert approve.json()["status"] == "approved"


def test_set_key_fills_stub_rationale(client, db_session, monkeypatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "test-stub-key")

    client.post("/events", json=_event("llm-key-move", 42.0))
    opened = client.post("/events", json=_event("llm-key-stop", 0.0, seconds=5))
    case_id = opened.json()["case_id"]
    assert case_id is not None

    db_session.expire_all()
    case = db_session.get(Case, case_id)
    assert case is not None
    assert case.rationale is not None
    assert "42" in case.rationale
    assert "0" in case.rationale
    assert "drone" in case.rationale.lower()

    listed = client.get("/cases").json()
    assert listed[0]["rationale"] == case.rationale
