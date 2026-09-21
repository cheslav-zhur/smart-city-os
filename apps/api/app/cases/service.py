from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.audit.service import (
    ACTION_APPROVE,
    ACTION_OUTDATED,
    ACTION_REJECT,
    ACTOR_SYSTEM,
    WHY_APPROVE,
    WHY_OUTDATED,
    WHY_REJECT,
    write_audit,
    write_audit_entry,
)
from app.drone.service import DRONE_IDLE, dispatch_after_approve
from app.models import Case, Event

SEGMENT_A = "A"
KIND_CRASH_DROP = "crash_drop"
KIND_SPEEDING = "speeding"
KIND_JAM = "jam"
EVENT_KINDS = (KIND_CRASH_DROP, KIND_SPEEDING, KIND_JAM)
MOVING_MIN = 0.0
COLLAPSE_MAX = 0.5
SPEEDING_MIN = 80.0
JAM_MAX = 5.0
JAM_SLOW_WINDOW = 3
JAM_PRIOR_WINDOW = 3
CASE_OPEN = "open"
CASE_APPROVED = "approved"
CASE_REJECTED = "rejected"
CASE_OUTDATED = "outdated"


class CaseNotFoundError(LookupError):
    """No case row for this id."""


class CaseAlreadyDecidedError(ValueError):
    """SQL CAS found zero open rows — already approved, rejected, or outdated."""


def maybe_open_case(session: Session, segment: str, kind: str) -> Case | None:
    """Open at most one open case when this event's kind matches its rule.

    The window is the shared speed tape on the segment, newest first. Kind
    selects the rule; it does not filter out samples of another kind.

    A matching rule displaces any current open in the same occupancy step,
    then inserts the new open. A non-matching event leaves the open slot.
    """
    existing = session.scalar(
        select(Case)
        .where(Case.segment == segment, Case.status == CASE_OPEN)
        .with_for_update()
    )
    samples = _recent_samples(session, segment, limit=JAM_SLOW_WINDOW + JAM_PRIOR_WINDOW)
    if not _rule_matches(kind, samples):
        return None

    if existing is not None:
        _displace_open_case(session, existing)

    case = Case(
        segment=segment,
        status=CASE_OPEN,
        drone_status=DRONE_IDLE,
        trigger_kind=kind,
    )
    session.add(case)
    session.flush()
    return case


def _displace_open_case(session: Session, case: Case) -> None:
    """Mark the locked open row outdated, audit, cancel pending. Drone stays idle."""
    case.status = CASE_OUTDATED
    case.drone_status = DRONE_IDLE
    session.flush()
    write_audit_entry(
        session,
        case_id=case.id,
        actor=ACTOR_SYSTEM,
        action=ACTION_OUTDATED,
        why=WHY_OUTDATED,
    )
    _cancel_pending_jobs(session, case.id)


def _recent_samples(session: Session, segment: str, limit: int) -> list[Event]:
    return list(
        session.scalars(
            select(Event)
            .where(Event.segment == segment)
            .order_by(Event.recorded_at.desc(), Event.id.desc())
            .limit(limit)
        ).all()
    )


def _rule_matches(kind: str, samples: list[Event]) -> bool:
    if kind == KIND_CRASH_DROP:
        return _is_collapse(samples)
    if kind == KIND_SPEEDING:
        return _is_speeding(samples)
    if kind == KIND_JAM:
        return _is_jam(samples)
    return False


def _is_collapse(samples: list[Event]) -> bool:
    """Last two samples: previous was moving, current has dropped."""
    if len(samples) < 2:
        return False
    current, previous = samples[0], samples[1]
    return previous.speed > MOVING_MIN and current.speed <= COLLAPSE_MAX


def _is_speeding(samples: list[Event]) -> bool:
    """Last sample is at or over the speeding threshold. No history required."""
    if not samples:
        return False
    return samples[0].speed >= SPEEDING_MIN


def _is_jam(samples: list[Event]) -> bool:
    """Slow stretch that just started, not a road that was already slow.

    Newest-first: the last three speeds are all at or under JAM_MAX, and at
    least one of the three before that was faster. A shorter tape does not open.
    """
    need = JAM_SLOW_WINDOW + JAM_PRIOR_WINDOW
    if len(samples) < need:
        return False
    slow = samples[:JAM_SLOW_WINDOW]
    prior = samples[JAM_SLOW_WINDOW:need]
    if any(sample.speed > JAM_MAX for sample in slow):
        return False
    return any(sample.speed > JAM_MAX for sample in prior)


def get_case(session: Session, case_id: int) -> Case | None:
    """Return one case row, or None if missing."""
    return session.get(Case, case_id)


def list_cases(session: Session) -> list[Case]:
    """All cases (open and decided), newest first by serial id."""
    return list(session.scalars(select(Case).order_by(Case.id.desc())).all())


def approve_case(session: Session, case_id: int) -> Case:
    """Approve an open case: drone stub + audit + cancel pending jobs."""
    case = _cas_decide(
        session,
        case_id,
        status=CASE_APPROVED,
    )
    dispatch_after_approve(case)
    write_audit(session, case.id, ACTION_APPROVE, WHY_APPROVE)
    _cancel_pending_jobs(session, case.id)
    return case


def reject_case(session: Session, case_id: int) -> Case:
    """Reject an open case: drone stays idle + audit + cancel pending jobs."""
    case = _cas_decide(
        session,
        case_id,
        status=CASE_REJECTED,
        drone_status=DRONE_IDLE,
    )
    write_audit(session, case.id, ACTION_REJECT, WHY_REJECT)
    _cancel_pending_jobs(session, case.id)
    return case


def _cas_decide(
    session: Session,
    case_id: int,
    *,
    status: str,
    drone_status: str | None = None,
) -> Case:
    """UPDATE … WHERE status='open'. Zero rows is already decided, not a Python check."""
    case = session.get(Case, case_id)
    if case is None:
        raise CaseNotFoundError(case_id)

    values: dict[str, str] = {"status": status}
    if drone_status is not None:
        values["drone_status"] = drone_status
    result = session.execute(
        update(Case)
        .where(Case.id == case_id, Case.status == CASE_OPEN)
        .values(**values)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount == 0:
        raise CaseAlreadyDecidedError(case_id)
    session.refresh(case)
    return case


def _cancel_pending_jobs(session: Session, case_id: int) -> None:
    # Imported here so the worker can load jobs.service without the drone stub.
    from app.jobs.service import cancel_pending_jobs

    cancel_pending_jobs(session, case_id)
