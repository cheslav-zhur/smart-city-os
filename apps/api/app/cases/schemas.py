from datetime import datetime

from pydantic import BaseModel


class CaseListItem(BaseModel):
    """Console case row: card fields only, no audit or timestamps."""

    id: int
    segment: str
    status: str
    drone_status: str
    dispatcher_opinion: str | None
    critic_opinion: str | None
    trigger_kind: str | None


class CaseDecisionOut(BaseModel):
    """Approve / reject response for the console."""

    id: int
    status: str
    drone_status: str


class AuditListItem(BaseModel):
    """One append-only audit row for the case card (KTD6)."""

    id: int
    actor: str
    action: str
    why: str | None
    created_at: datetime
