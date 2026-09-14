from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Case, Event

SEGMENT_A = "A"
MOVING_MIN = 0.0
COLLAPSE_MAX = 0.5
CASE_OPEN = "open"


def maybe_open_on_collapse(session: Session, segment: str) -> Case | None:
    """Open at most one open case when the last two samples collapse."""
    existing = session.scalar(
        select(Case).where(Case.segment == segment, Case.status == CASE_OPEN)
    )
    if existing is not None:
        return None

    samples = session.scalars(
        select(Event)
        .where(Event.segment == segment)
        .order_by(Event.recorded_at.desc(), Event.id.desc())
        .limit(2)
    ).all()
    if len(samples) < 2:
        return None

    current, previous = samples[0], samples[1]
    if previous.speed <= MOVING_MIN or current.speed > COLLAPSE_MAX:
        return None

    case = Case(segment=segment, status=CASE_OPEN, drone_status="idle")
    session.add(case)
    session.flush()
    return case


def list_cases(session: Session) -> list[Case]:
    """All cases (open and decided), newest first by serial id."""
    return list(session.scalars(select(Case).order_by(Case.id.desc())).all())
