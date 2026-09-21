"""Job enqueue, lease steal, and leftover persist after decide."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select

from app.cases.service import CaseAlreadyDecidedError, approve_case, reject_case
from app.db import SessionLocal
from app.jobs.service import (
    PERSIST_CANCELLED,
    PERSIST_NOOP,
    claim_job,
    finish_stub_job,
    persist_job_result,
)
from app.models import (
    JOB_CANCELLED,
    JOB_DONE,
    JOB_PENDING,
    JOB_RUNNING,
    Case,
    Job,
)


def _event(event_id: str, speed: float, seconds: int = 0) -> dict:
    return {
        "event_id": event_id,
        "segment": "A",
        "speed": speed,
        "recorded_at": (
            datetime(2026, 9, 11, 5, 0, tzinfo=UTC) + timedelta(seconds=seconds)
        ).isoformat(),
    }


def _open_collapse(client) -> int:
    client.post("/events", json=_event("job-move", 40.0))
    opened = client.post("/events", json=_event("job-stop", 0.0, seconds=5))
    case_id = opened.json()["case_id"]
    assert case_id is not None
    return case_id


def test_collapse_ingest_enqueues_pending_job(client, db_session) -> None:
    case_id = _open_collapse(client)

    job = db_session.scalar(select(Job))
    assert job is not None
    assert job.case_id == case_id
    assert job.status == JOB_PENDING
    assert db_session.scalar(select(func.count()).select_from(Job)) == 1


def test_duplicate_event_id_does_not_insert_a_second_job(client, db_session) -> None:
    case_id = _open_collapse(client)
    duplicate = client.post("/events", json=_event("job-stop", 0.0, seconds=5))

    assert duplicate.status_code == 200
    assert duplicate.json()["duplicate"] is True
    assert duplicate.json()["case_id"] is None
    assert db_session.scalar(select(func.count()).select_from(Job)) == 1
    job = db_session.scalar(select(Job))
    assert job is not None
    assert job.case_id == case_id


def test_worker_unset_key_finishes_done_with_null_opinions(
    client, db_session, monkeypatch
) -> None:
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    case_id = _open_collapse(client)

    claimed = claim_job(db_session)
    db_session.commit()
    assert claimed is not None
    assert claimed.case_id == case_id

    status = finish_stub_job(db_session, claimed)
    db_session.commit()
    assert status == JOB_DONE

    db_session.expire_all()
    job = db_session.get(Job, claimed.job_id)
    case = db_session.get(Case, case_id)
    assert job is not None
    assert job.status == JOB_DONE
    assert case is not None
    assert case.dispatcher_opinion is None
    assert case.critic_opinion is None
    assert case.status == "open"

    approve = client.post(f"/cases/{case_id}/approve")
    assert approve.status_code == 200


def test_expired_lease_steal_bumps_version_and_stale_complete_is_noop(
    client, db_session
) -> None:
    _open_collapse(client)

    with SessionLocal() as worker_a:
        claimed_a = claim_job(worker_a)
        worker_a.commit()
    assert claimed_a is not None
    assert claimed_a.lease_version == 1

    job = db_session.scalar(select(Job))
    assert job is not None
    job.lease_expires_at = datetime.now(UTC) - timedelta(seconds=1)
    db_session.commit()

    with SessionLocal() as worker_b:
        claimed_b = claim_job(worker_b)
        worker_b.commit()
    assert claimed_b is not None
    assert claimed_b.job_id == claimed_a.job_id
    assert claimed_b.lease_version == 2

    with SessionLocal() as worker_a:
        stale = persist_job_result(
            worker_a,
            job_id=claimed_a.job_id,
            lease_version=claimed_a.lease_version,
            dispatcher_opinion="late dispatcher",
            critic_opinion="late critic",
        )
        worker_a.commit()
    assert stale == PERSIST_NOOP

    db_session.expire_all()
    job = db_session.get(Job, claimed_a.job_id)
    case = db_session.get(Case, claimed_a.case_id)
    assert job is not None
    assert job.status == JOB_RUNNING
    assert job.lease_version == 2
    assert case is not None
    assert case.dispatcher_opinion is None
    assert case.critic_opinion is None

    with SessionLocal() as worker_b:
        done = finish_stub_job(worker_b, claimed_b)
        worker_b.commit()
    assert done == JOB_DONE


def test_claim_then_approve_then_persist_leaves_opinions_null(
    client, db_session
) -> None:
    case_id = _open_collapse(client)

    claimed = claim_job(db_session)
    db_session.commit()
    assert claimed is not None
    assert claimed.lease_version == 1

    approve = client.post(f"/cases/{case_id}/approve")
    assert approve.status_code == 200
    assert approve.json()["drone_status"] == "on_site"

    db_session.expire_all()
    running = db_session.get(Job, claimed.job_id)
    assert running is not None
    assert running.status == JOB_RUNNING

    leftover = persist_job_result(
        db_session,
        job_id=claimed.job_id,
        lease_version=claimed.lease_version,
        dispatcher_opinion="too late",
        critic_opinion="also late",
    )
    db_session.commit()
    assert leftover == PERSIST_CANCELLED

    db_session.expire_all()
    job = db_session.get(Job, claimed.job_id)
    case = db_session.get(Case, case_id)
    assert job is not None
    assert job.status == JOB_CANCELLED
    assert case is not None
    assert case.dispatcher_opinion is None
    assert case.critic_opinion is None
    assert case.status == "approved"
    assert case.drone_status == "on_site"


def test_claim_then_displace_then_persist_leaves_opinions_null(
    client, db_session
) -> None:
    case_id = _open_collapse(client)

    claimed = claim_job(db_session)
    db_session.commit()
    assert claimed is not None

    case = db_session.get(Case, case_id)
    assert case is not None
    case.created_at = datetime.now(UTC) - timedelta(seconds=21)
    db_session.commit()

    opened = client.post(
        "/events",
        json={
            "event_id": "job-spd",
            "segment": "A",
            "speed": 90.0,
            "kind": "speeding",
            "recorded_at": (
                datetime(2026, 9, 11, 5, 0, tzinfo=UTC) + timedelta(seconds=20)
            ).isoformat(),
        },
    )
    assert opened.status_code == 201
    assert opened.json()["case_id"] is not None

    leftover = persist_job_result(
        db_session,
        job_id=claimed.job_id,
        lease_version=claimed.lease_version,
        dispatcher_opinion="too late",
        critic_opinion="also late",
    )
    db_session.commit()
    assert leftover == PERSIST_CANCELLED

    db_session.expire_all()
    job = db_session.get(Job, claimed.job_id)
    case = db_session.get(Case, case_id)
    assert job is not None
    assert job.status == JOB_CANCELLED
    assert case is not None
    assert case.dispatcher_opinion is None
    assert case.critic_opinion is None
    assert case.status == "outdated"
    assert case.drone_status == "idle"


def test_approve_cancels_pending_job_only(client, db_session) -> None:
    case_id = _open_collapse(client)
    job = db_session.scalar(select(Job))
    assert job is not None
    assert job.status == JOB_PENDING

    reject = client.post(f"/cases/{case_id}/reject")
    assert reject.status_code == 200

    db_session.expire_all()
    job = db_session.scalar(select(Job))
    assert job is not None
    assert job.status == JOB_CANCELLED


def test_second_decide_is_409_via_sql_cas(client) -> None:
    case_id = _open_collapse(client)

    with SessionLocal() as first:
        approve_case(first, case_id)
        first.commit()

    with SessionLocal() as second:
        with pytest.raises(CaseAlreadyDecidedError):
            reject_case(second, case_id)
        second.rollback()

    via_http = client.post(f"/cases/{case_id}/reject")
    assert via_http.status_code == 409
