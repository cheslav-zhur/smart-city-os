from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.audit.service import ACTION_APPROVE, ACTION_REJECT, WHY_APPROVE, WHY_REJECT
from app.models import AuditEntry, Case


def _event(event_id: str, speed: float, seconds: int = 0) -> dict:
    return {
        "event_id": event_id,
        "segment": "A",
        "speed": speed,
        "recorded_at": (
            datetime(2026, 9, 11, 5, 0, tzinfo=UTC) + timedelta(seconds=seconds)
        ).isoformat(),
    }


def _open_case(client) -> int:
    client.post("/events", json=_event("hitl-move", 40.0))
    response = client.post("/events", json=_event("hitl-stop", 0.0, seconds=5))
    case_id = response.json()["case_id"]
    assert case_id is not None
    return case_id


def test_approve_sets_drone_and_writes_audit(client, db_session) -> None:
    case_id = _open_case(client)

    response = client.post(f"/cases/{case_id}/approve")

    assert response.status_code == 200
    assert response.json() == {
        "id": case_id,
        "status": "approved",
        "drone_status": "on_site",
    }
    case = db_session.get(Case, case_id)
    assert case is not None
    assert case.status == "approved"
    assert case.drone_status == "on_site"
    entry = db_session.scalar(
        select(AuditEntry).where(AuditEntry.case_id == case_id)
    )
    assert entry is not None
    assert entry.actor == "demo-operator"
    assert entry.action == ACTION_APPROVE
    assert entry.why == WHY_APPROVE


def test_reject_keeps_drone_idle_and_writes_audit(client, db_session) -> None:
    case_id = _open_case(client)

    response = client.post(f"/cases/{case_id}/reject")

    assert response.status_code == 200
    assert response.json() == {
        "id": case_id,
        "status": "rejected",
        "drone_status": "idle",
    }
    case = db_session.get(Case, case_id)
    assert case is not None
    assert case.status == "rejected"
    assert case.drone_status == "idle"
    entry = db_session.scalar(
        select(AuditEntry).where(AuditEntry.case_id == case_id)
    )
    assert entry is not None
    assert entry.action == ACTION_REJECT
    assert entry.why == WHY_REJECT


def test_unknown_case_is_404(client) -> None:
    response = client.post("/cases/99999/approve")
    assert response.status_code == 404


def test_second_decision_is_409(client) -> None:
    case_id = _open_case(client)
    first = client.post(f"/cases/{case_id}/approve")
    second = client.post(f"/cases/{case_id}/reject")

    assert first.status_code == 200
    assert second.status_code == 409


def test_approve_after_grace_while_still_open_is_hitl(client, db_session) -> None:
    """Grace elapsed but nothing displaced yet: Send is still ordinary HITL."""
    case_id = _open_case(client)
    case = db_session.get(Case, case_id)
    assert case is not None
    case.created_at = datetime.now(UTC) - timedelta(seconds=21)
    db_session.commit()

    response = client.post(f"/cases/{case_id}/approve")
    assert response.status_code == 200
    assert response.json()["status"] == "approved"


def test_decide_on_outdated_is_409(client, db_session) -> None:
    case_id = _open_case(client)
    case = db_session.get(Case, case_id)
    assert case is not None
    case.created_at = datetime.now(UTC) - timedelta(seconds=21)
    db_session.commit()

    displaced = client.post(
        "/events",
        json={
            "event_id": "hitl-spd",
            "segment": "A",
            "speed": 90.0,
            "kind": "speeding",
            "recorded_at": (
                datetime(2026, 9, 11, 5, 0, tzinfo=UTC) + timedelta(seconds=20)
            ).isoformat(),
        },
    )
    assert displaced.status_code == 201
    assert displaced.json()["case_id"] is not None
    assert displaced.json()["case_id"] != case_id

    db_session.expire_all()
    outdated = db_session.get(Case, case_id)
    assert outdated is not None
    assert outdated.status == "outdated"

    approve = client.post(f"/cases/{case_id}/approve")
    reject = client.post(f"/cases/{case_id}/reject")
    assert approve.status_code == 409
    assert reject.status_code == 409
