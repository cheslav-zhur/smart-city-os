from datetime import UTC, datetime, timedelta


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
    assert set(item.keys()) == {"id", "segment", "status", "drone_status"}
    assert item == {
        "id": case_id,
        "segment": "A",
        "status": "open",
        "drone_status": "idle",
    }

    events = client.get("/events")
    assert events.status_code == 200
    tape = events.json()
    assert [row["event_id"] for row in tape] == ["sim-011", "sim-010"]
    for row in tape:
        assert set(row.keys()) == {"event_id", "segment", "speed", "recorded_at"}
        assert row["segment"] == "A"
    assert tape[0]["speed"] == 0.0
    assert tape[1]["speed"] == 40.0
