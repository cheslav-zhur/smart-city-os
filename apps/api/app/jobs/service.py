"""Enqueue, claim, and fenced persist for one job row per case.

This module must not import app.drone.service or approve/reject. The worker
process loads it; flight stays in the API.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, or_, select, update
from sqlalchemy.orm import Session

from app.models import (
    JOB_CANCELLED,
    JOB_DONE,
    JOB_PENDING,
    JOB_RUNNING,
    Case,
    Job,
)

# Named tunables, same class as opening thresholds. Not ADR-level.
JOB_LEASE_SECONDS = 30
# Must match cases.service.CASE_OPEN. Do not import that module here: it pulls in
# the drone stub, which the worker process must not load.
_CASE_OPEN = "open"

PERSIST_NOOP = "noop"
PERSIST_DONE = "done"
PERSIST_CANCELLED = "cancelled"


@dataclass(frozen=True)
class ClaimedJob:
    job_id: int
    case_id: int
    lease_version: int


def enqueue_pending_job(session: Session, case: Case) -> Job:
    """Insert the one pending job for a newly opened case."""
    job = Job(case_id=case.id, status=JOB_PENDING)
    session.add(job)
    session.flush()
    return job


def cancel_pending_jobs(session: Session, case_id: int) -> None:
    """Cancel leftover queued work. Leave running rows for fenced persist."""
    session.execute(
        update(Job)
        .where(Job.case_id == case_id, Job.status == JOB_PENDING)
        .values(status=JOB_CANCELLED)
        .execution_options(synchronize_session=False)
    )


def claim_job(session: Session) -> ClaimedJob | None:
    """Take one pending or expired-running row. Caller commits this short txn."""
    now = datetime.now(UTC)
    job = session.scalar(
        select(Job)
        .where(
            or_(
                Job.status == JOB_PENDING,
                and_(
                    Job.status == JOB_RUNNING,
                    Job.lease_expires_at <= now,
                ),
            )
        )
        .order_by(Job.id)
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    if job is None:
        return None

    job.status = JOB_RUNNING
    job.lease_version += 1
    job.attempts += 1
    job.lease_expires_at = now + timedelta(seconds=JOB_LEASE_SECONDS)
    session.flush()
    return ClaimedJob(
        job_id=job.id,
        case_id=job.case_id,
        lease_version=job.lease_version,
    )


def persist_job_result(
    session: Session,
    *,
    job_id: int,
    lease_version: int,
    dispatcher_opinion: str | None,
    critic_opinion: str | None,
) -> str:
    """Write both opinion columns or neither, then a terminal job status.

    Fencing is lease_version plus status='running'. If the case is no longer
    open, the job becomes cancelled and the case is not mutated. A stale
    lease is a no-op.
    """
    job = session.scalar(
        select(Job)
        .where(
            Job.id == job_id,
            Job.lease_version == lease_version,
            Job.status == JOB_RUNNING,
        )
        .with_for_update()
    )
    if job is None:
        return PERSIST_NOOP

    case = session.scalar(
        select(Case)
        .where(Case.id == job.case_id, Case.status == _CASE_OPEN)
        .with_for_update()
    )
    if case is None:
        job.status = JOB_CANCELLED
        job.lease_expires_at = None
        session.flush()
        return PERSIST_CANCELLED

    case.dispatcher_opinion = dispatcher_opinion
    case.critic_opinion = critic_opinion
    job.status = JOB_DONE
    job.lease_expires_at = None
    session.flush()
    return PERSIST_DONE


def finish_stub_job(session: Session, claimed: ClaimedJob) -> str:
    """Complete a claimed job with empty opinions. The graph is V1-U5."""
    return persist_job_result(
        session,
        job_id=claimed.job_id,
        lease_version=claimed.lease_version,
        dispatcher_opinion=None,
        critic_opinion=None,
    )
