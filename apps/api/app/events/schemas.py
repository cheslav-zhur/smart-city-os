from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.cases.service import SEGMENT_A


class EventIn(BaseModel):
    event_id: str = Field(min_length=1, max_length=255)
    segment: str
    speed: float
    recorded_at: datetime

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
