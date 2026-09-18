from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.cases.service import SEGMENT_A, maybe_open_case
from app.events.schemas import EventIn
from app.llm.service import maybe_fill_rationale
from app.models import Event


def ingest_event(session: Session, payload: EventIn) -> tuple[Event, int | None, bool]:
    existing = session.scalar(select(Event).where(Event.event_id == payload.event_id))
    if existing is not None:
        return existing, None, True

    event = Event(
        event_id=payload.event_id,
        segment=payload.segment,
        kind=payload.kind,
        speed=payload.speed,
        recorded_at=payload.recorded_at,
    )
    session.add(event)
    try:
        session.flush()
    except IntegrityError:
        session.rollback()
        existing = session.scalar(select(Event).where(Event.event_id == payload.event_id))
        if existing is None:
            raise
        return existing, None, True

    case = maybe_open_case(session, event.segment, event.kind)
    if case is not None:
        maybe_fill_rationale(session, case)
    return event, case.id if case is not None else None, False


def list_segment_a_events(session: Session) -> list[Event]:
    """Speed tape for segment A, newest recorded_at first (then id)."""
    return list(
        session.scalars(
            select(Event)
            .where(Event.segment == SEGMENT_A)
            .order_by(Event.recorded_at.desc(), Event.id.desc())
        ).all()
    )
