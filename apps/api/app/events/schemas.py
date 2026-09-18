from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.cases.service import KIND_CRASH_DROP, SEGMENT_A

EventKind = Literal["crash_drop", "speeding", "jam"]


class EventIn(BaseModel):
    event_id: str = Field(min_length=1, max_length=255)
    segment: str
    speed: float
    recorded_at: datetime
    kind: EventKind = KIND_CRASH_DROP

    @field_validator("segment")
    @classmethod
    def segment_is_a(cls, value: str) -> str:
        if value != SEGMENT_A:
            raise ValueError("only segment A is supported")
        return value


class EventOut(BaseModel):
    event_id: str
    segment: str
    speed: float
    recorded_at: datetime
    duplicate: bool
    case_id: int | None


class EventTapeItem(BaseModel):
    """Console tape row: speed and kind, not the ingest echo."""

    event_id: str
    segment: str
    kind: EventKind
    speed: float
    recorded_at: datetime
