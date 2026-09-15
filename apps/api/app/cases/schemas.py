from pydantic import BaseModel


class CaseListItem(BaseModel):
    """Console case row: card fields only, no audit or timestamps."""

    id: int
    segment: str
    status: str
    drone_status: str
    rationale: str | None
