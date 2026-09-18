"""Opening rules for crash_drop, speeding, and jam. No LLM key required."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from app.models import Case, Event


def _event(
    event_id: str,
    speed: float,
    seconds: int = 0,
    kind: str | None = None,
) -> dict:
    payload = {
        "event_id": event_id,
        "segment": "A",
        "speed": speed,
        "recorded_at": (
            datetime(2026, 9, 11, 5, 0, tzinfo=UTC) + timedelta(seconds=seconds)
        ).isoformat(),
    }
    if kind is not None:
        payload["kind"] = kind
    return payload


def test_crash_drop_collapse_sets_trigger_kind(client, db_session) -> None:
    client.post("/events", json=_event("drop-1", 40.0, kind="crash_drop"))
    stopped = client.post(
        "/events", json=_event("drop-2", 0.0, seconds=5, kind="crash_drop")
    )

    assert stopped.status_code == 201
    assert stopped.json()["case_id"] is not None
    case = db_session.scalar(select(Case))
    assert case is not None
    assert case.trigger_kind == "crash_drop"


def test_speeding_opens_when_none_is_open(client, db_session) -> None:
    opened = client.post("/events", json=_event("spd-1", 80.0, kind="speeding"))

    assert opened.status_code == 201
    assert opened.json()["case_id"] is not None
    case = db_session.scalar(select(Case))
    assert case is not None
    assert case.trigger_kind == "speeding"
    assert db_session.scalar(select(func.count()).select_from(Case)) == 1


def test_jam_window_opens_on_the_shared_tape(client, db_session) -> None:
    """Prior samples may be another kind; the window is not filtered by kind."""
    prior = [40.0, 38.0, 30.0, 4.0, 3.0]
    for index, speed in enumerate(prior):
        response = client.post(
            "/events",
            json=_event(f"jam-{index}", speed, seconds=index, kind="crash_drop"),
        )
        assert response.json()["case_id"] is None

    opened = client.post(
        "/events", json=_event("jam-last", 2.0, seconds=5, kind="jam")
    )

    assert opened.status_code == 201
    assert opened.json()["case_id"] is not None
    case = db_session.scalar(select(Case))
    assert case is not None
    assert case.trigger_kind == "jam"


def test_short_jam_tape_does_not_open(client, db_session) -> None:
    speeds = [40.0, 4.0, 3.0, 2.0]
    last = None
    for index, speed in enumerate(speeds):
        last = client.post(
            "/events",
            json=_event(
                f"short-{index}",
                speed,
                seconds=index,
                kind="jam" if index == len(speeds) - 1 else "crash_drop",
            ),
        )

    assert last is not None
    assert last.status_code == 201
    assert last.json()["case_id"] is None
    assert db_session.scalar(select(func.count()).select_from(Case)) == 0


def test_speeding_while_crash_case_is_open_does_not_double_open(
    client, db_session
) -> None:
    client.post("/events", json=_event("mix-1", 40.0, kind="crash_drop"))
    crashed = client.post(
        "/events", json=_event("mix-2", 0.0, seconds=5, kind="crash_drop")
    )
    speeding = client.post(
        "/events", json=_event("mix-3", 90.0, seconds=10, kind="speeding")
    )

    assert crashed.json()["case_id"] is not None
    assert speeding.status_code == 201
    assert speeding.json()["case_id"] is None
    assert db_session.scalar(select(func.count()).select_from(Case)) == 1
    assert db_session.scalar(select(func.count()).select_from(Event)) == 3
    stored = db_session.scalar(select(Event).where(Event.event_id == "mix-3"))
    assert stored is not None
    assert stored.kind == "speeding"
    case = db_session.scalar(select(Case))
    assert case is not None
    assert case.trigger_kind == "crash_drop"


def test_unknown_kind_is_422(client, db_session) -> None:
    response = client.post("/events", json=_event("bad-1", 40.0, kind="flood"))

    assert response.status_code == 422
    assert db_session.scalar(select(func.count()).select_from(Event)) == 0
