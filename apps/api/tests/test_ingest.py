from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from app.models import Case, Event


def _event(event_id: str, speed: float, seconds: int = 0) -> dict:
    return {
        "event_id": event_id,
        "segment": "A",
        "speed": speed,
        "recorded_at": (datetime(2026, 9, 11, 5, 0, tzinfo=UTC) + timedelta(seconds=seconds)).isoformat(),
    }


def test_duplicate_event_id_writes_one_row(client, db_session) -> None:
    first = client.post("/events", json=_event("sim-001", 40.0))
    second = client.post("/events", json=_event("sim-001", 99.0, seconds=10))

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["duplicate"] is True
    assert second.json()["speed"] == 40.0
    assert db_session.scalar(select(func.count()).select_from(Event)) == 1


def test_collapse_sequence_opens_one_case(client, db_session) -> None:
    moving = client.post("/events", json=_event("sim-010", 40.0))
    stopped = client.post("/events", json=_event("sim-011", 0.0, seconds=5))

    assert moving.status_code == 201
    assert moving.json()["case_id"] is None
    assert stopped.status_code == 201
    assert stopped.json()["case_id"] is not None
    assert db_session.scalar(select(func.count()).select_from(Case)) == 1
    case = db_session.scalar(select(Case))
    assert case is not None
    assert case.trigger_kind == "crash_drop"

    again_moving = client.post("/events", json=_event("sim-012", 35.0, seconds=10))
    again_stopped = client.post("/events", json=_event("sim-013", 0.2, seconds=15))
    assert again_moving.json()["case_id"] is None
    assert again_stopped.json()["case_id"] is None
    assert db_session.scalar(select(func.count()).select_from(Case)) == 1


def test_no_collapse_opens_no_case(client, db_session) -> None:
    client.post("/events", json=_event("sim-020", 40.0))
    still_moving = client.post("/events", json=_event("sim-021", 38.0, seconds=5))

    assert still_moving.status_code == 201
    assert still_moving.json()["case_id"] is None
    assert db_session.scalar(select(func.count()).select_from(Case)) == 0


def test_unknown_segment_is_rejected(client, db_session) -> None:
    payload = _event("sim-030", 40.0)
    payload["segment"] = "B"
    response = client.post("/events", json=payload)

    assert response.status_code == 422
    assert db_session.scalar(select(func.count()).select_from(Event)) == 0
