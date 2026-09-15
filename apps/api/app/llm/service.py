"""Optional rationale for an open case.

Tools are plain functions: read recent speeds, write draft text.
No model HTTP and no fly() on MVP — a set LLM_API_KEY only enables the stub draft.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Case, Event
from app.settings import get_settings


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


def _stub_draft(segment: str, samples: list[Event]) -> str:
    if len(samples) >= 2:
        current, previous = samples[0], samples[1]
        return (
            f"Speed on {segment} dropped from {previous.speed:g} to "
            f"{current.speed:g}; suggest drone inspection."
        )
    return f"Collapse on {segment}; suggest drone inspection."


def maybe_fill_rationale(session: Session, case: Case) -> None:
    """If LLM_API_KEY is set, fill rationale from recent events; else leave null."""
    key = get_settings().llm_api_key
    if not key:
        return
    samples = read_recent_events(session, case.segment, limit=2)
    write_draft(case, _stub_draft(case.segment, samples))
