from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db import get_session
from app.events.schemas import EventIn, EventOut, EventTapeItem
from app.events.service import ingest_event, list_segment_a_events

router = APIRouter(tags=["events"])


@router.get("/events")
def get_events(
    session: Annotated[Session, Depends(get_session)],
) -> list[EventTapeItem]:
    return [
        EventTapeItem(
            event_id=event.event_id,
            segment=event.segment,
            speed=event.speed,
            recorded_at=event.recorded_at,
        )
        for event in list_segment_a_events(session)
    ]


@router.post("/events")
def post_event(
    payload: EventIn, session: Annotated[Session, Depends(get_session)]
) -> JSONResponse:
    event, case_id, duplicate = ingest_event(session, payload)
    body = EventOut(
        event_id=event.event_id,
        segment=event.segment,
        speed=event.speed,
        recorded_at=event.recorded_at,
        duplicate=duplicate,
        case_id=case_id,
    )
    return JSONResponse(
        content=body.model_dump(mode="json"),
        status_code=200 if duplicate else 201,
    )
