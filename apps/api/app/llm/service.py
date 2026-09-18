"""Optional card tools. Ingest must not call these; the worker graph is V1-U5.

Tools are plain functions: read recent speeds, write draft text. No fly().
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Case, Event


def read_recent_events(
    session: Session, segment: str, *, limit: int = 2
) -> list[Event]:
    """Read tool: newest speed samples for the segment."""
    return list(
        session.scalars(
            select(Event)
            .where(Event.segment == segment)
            .order_by(Event.recorded_at.desc(), Event.id.desc())
            .limit(limit)
        ).all()
    )


def write_draft(case: Case, text: str) -> None:
    """Write tool: store draft why on the case card (not audit.why)."""
    case.rationale = text
