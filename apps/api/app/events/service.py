from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.cases.service import maybe_open_on_collapse
from app.events.schemas import EventIn
from app.models import Event


def ingest_event(session: Session, payload: EventIn) -> tuple[Event, int | None, bool]:
    existing = session.scalar(select(Event).where(Event.event_id == payload.event_id))
    if existing is not None:
        return existing, None, True

    event = Event(
        event_id=payload.event_id,
        segment=payload.segment,
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

    case = maybe_open_on_collapse(session, event.segment)
    return event, case.id if case is not None else None, False
