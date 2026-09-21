"""Opening rules for crash_drop, speeding, and jam. No LLM key required."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from app.models import JOB_CANCELLED, JOB_PENDING, AuditEntry, Case, Event, Job


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


def _age_past_grace(db_session, case_id: int) -> None:
    """Move created_at behind the ~20s grace window. Do not sleep."""
    case = db_session.get(Case, case_id)
    assert case is not None
    case.created_at = datetime.now(UTC) - timedelta(seconds=21)
    db_session.commit()
    db_session.expire_all()


def test_in_grace_matching_kind_holds_the_open_slot(client, db_session) -> None:
    """AE1: inside grace a later kind is stored and does not open a second case."""
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
    case = db_session.get(Case, crashed.json()["case_id"])
    assert case is not None
    assert case.status == "open"
    assert case.trigger_kind == "crash_drop"


def test_after_grace_matching_jam_displaces_open_to_outdated(
    client, db_session
) -> None:
    """AE2: after grace a matching jam opens case 2 and marks case 1 outdated."""
    client.post("/events", json=_event("age-1", 40.0, kind="crash_drop"))
    crashed = client.post(
        "/events", json=_event("age-2", 0.0, seconds=5, kind="crash_drop")
    )
    case_id = crashed.json()["case_id"]
    assert case_id is not None
    _age_past_grace(db_session, case_id)

    fillers = [40.0, 38.0, 30.0, 4.0, 3.0]
    for index, speed in enumerate(fillers):
        held = client.post(
            "/events",
            json=_event(f"age-jam-{index}", speed, seconds=20 + index, kind="crash_drop"),
        )
        assert held.json()["case_id"] is None

    opened = client.post(
        "/events", json=_event("age-jam-last", 2.0, seconds=30, kind="jam")
    )
    assert opened.status_code == 201
    new_id = opened.json()["case_id"]
    assert new_id is not None
    assert new_id != case_id

    db_session.expire_all()
    old = db_session.get(Case, case_id)
    new = db_session.get(Case, new_id)
    assert old is not None
    assert old.status == "outdated"
    assert old.drone_status == "idle"
    assert new is not None
    assert new.status == "open"
    assert new.trigger_kind == "jam"
    old_job = db_session.scalar(select(Job).where(Job.case_id == case_id))
    new_job = db_session.scalar(select(Job).where(Job.case_id == new_id))
    assert old_job is not None
    assert old_job.status == JOB_CANCELLED
    assert new_job is not None
    assert new_job.status == JOB_PENDING
    assert db_session.scalar(
        select(func.count()).select_from(Case).where(Case.status == "open")
    ) == 1

    audit = list(
        db_session.scalars(
            select(AuditEntry).where(AuditEntry.case_id == case_id)
        ).all()
    )
    assert len(audit) == 1
    assert audit[0].actor == "system"
    assert audit[0].action == "outdated"


def test_dismiss_inside_grace_is_rejected_not_outdated(client, db_session) -> None:
    """AE4: operator dismiss beats displace; a later kind may open a new case."""
    client.post("/events", json=_event("d1", 40.0, kind="crash_drop"))
    crashed = client.post(
        "/events", json=_event("d2", 0.0, seconds=5, kind="crash_drop")
    )
    case_id = crashed.json()["case_id"]
    assert case_id is not None

    dismissed = client.post(f"/cases/{case_id}/reject")
    assert dismissed.status_code == 200

    later = client.post("/events", json=_event("d3", 90.0, seconds=10, kind="speeding"))
    assert later.status_code == 201
    new_id = later.json()["case_id"]
    assert new_id is not None
    assert new_id != case_id

    db_session.expire_all()
    first = db_session.get(Case, case_id)
    assert first is not None
    assert first.status == "rejected"
    assert first.status != "outdated"


def test_two_matching_posts_after_grace_keep_one_open(client, db_session) -> None:
    client.post("/events", json=_event("race-1", 40.0, kind="crash_drop"))
    crashed = client.post(
        "/events", json=_event("race-2", 0.0, seconds=5, kind="crash_drop")
    )
    case_id = crashed.json()["case_id"]
    assert case_id is not None
    _age_past_grace(db_session, case_id)

    first = client.post("/events", json=_event("race-3", 90.0, seconds=20, kind="speeding"))
    second = client.post(
        "/events", json=_event("race-4", 95.0, seconds=21, kind="speeding")
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["case_id"] is not None
    assert second.json()["case_id"] is None
    assert db_session.scalar(select(func.count()).select_from(Event)) == 4
    assert db_session.scalar(
        select(func.count()).select_from(Case).where(Case.status == "open")
    ) == 1


def test_unknown_kind_is_422(client, db_session) -> None:
    response = client.post("/events", json=_event("bad-1", 40.0, kind="flood"))

    assert response.status_code == 422
    assert db_session.scalar(select(func.count()).select_from(Event)) == 0
