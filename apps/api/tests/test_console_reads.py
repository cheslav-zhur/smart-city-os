from datetime import UTC, datetime, timedelta

from app.audit.service import ACTION_APPROVE, WHY_APPROVE


def _event(event_id: str, speed: float, seconds: int = 0) -> dict:
    return {
        "event_id": event_id,
        "segment": "A",
        "speed": speed,
        "recorded_at": (
            datetime(2026, 9, 11, 5, 0, tzinfo=UTC) + timedelta(seconds=seconds)
        ).isoformat(),
    }


def test_empty_db_lists_are_empty(client) -> None:
    cases = client.get("/cases")
    events = client.get("/events")

    assert cases.status_code == 200
    assert cases.json() == []
    assert events.status_code == 200
    assert events.json() == []


def test_collapse_ingest_appears_on_console_lists(client) -> None:
    moving = client.post("/events", json=_event("sim-010", 40.0))
    stopped = client.post("/events", json=_event("sim-011", 0.0, seconds=5))
    assert moving.status_code == 201
    assert stopped.status_code == 201
    case_id = stopped.json()["case_id"]
    assert case_id is not None

    cases = client.get("/cases")
    assert cases.status_code == 200
    body = cases.json()
    assert len(body) == 1
    item = body[0]
    assert set(item.keys()) == {
        "id",
        "segment",
        "status",
        "drone_status",
        "dispatcher_opinion",
        "critic_opinion",
    }
    assert item == {
        "id": case_id,
        "segment": "A",
        "status": "open",
        "drone_status": "idle",
        "dispatcher_opinion": None,
        "critic_opinion": None,
    }

    events = client.get("/events")
    assert events.status_code == 200
    tape = events.json()
    assert [row["event_id"] for row in tape] == ["sim-011", "sim-010"]
    for row in tape:
        assert set(row.keys()) == {
            "event_id",
            "segment",
            "kind",
            "speed",
            "recorded_at",
        }
        assert row["segment"] == "A"
        assert row["kind"] == "crash_drop"
    assert tape[0]["speed"] == 0.0
    assert tape[1]["speed"] == 40.0


def test_audit_get_after_approve_includes_operator_row(client) -> None:
    client.post("/events", json=_event("aud-move", 40.0))
    opened = client.post("/events", json=_event("aud-stop", 0.0, seconds=5))
    case_id = opened.json()["case_id"]
    assert case_id is not None

    empty = client.get(f"/cases/{case_id}/audit")
    assert empty.status_code == 200
    assert empty.json() == []

    approve = client.post(f"/cases/{case_id}/approve")
    assert approve.status_code == 200

    audit = client.get(f"/cases/{case_id}/audit")
    assert audit.status_code == 200
    body = audit.json()
    assert len(body) == 1
    row = body[0]
    assert set(row.keys()) == {"id", "actor", "action", "why", "created_at"}
    assert row["actor"] == "demo-operator"
    assert row["action"] == ACTION_APPROVE
    assert row["why"] == WHY_APPROVE
    assert isinstance(row["id"], int)
    assert isinstance(row["created_at"], str)


def test_audit_unknown_case_is_404(client) -> None:
    response = client.get("/cases/99999/audit")
    assert response.status_code == 404
