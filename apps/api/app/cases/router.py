from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.audit.service import (
    ACTION_APPROVE,
    ACTION_REJECT,
    WHY_APPROVE,
    WHY_REJECT,
    write_audit,
)
from app.cases.service import CASE_OPEN
from app.db import get_session
from app.drone.service import DRONE_IDLE, dispatch_after_approve
from app.models import Case

router = APIRouter()

CASE_APPROVED = "approved"
CASE_REJECTED = "rejected"


def _get_open_case(session: Session, case_id: int) -> Case:
    case = session.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="case not found")
    if case.status != CASE_OPEN:
        raise HTTPException(status_code=409, detail="case already decided")
    return case


@router.post("/cases/{case_id}/approve")
def approve_case(
    case_id: int, session: Annotated[Session, Depends(get_session)]
) -> dict:
    case = _get_open_case(session, case_id)
    case.status = CASE_APPROVED
    dispatch_after_approve(case)
    write_audit(session, case.id, ACTION_APPROVE, WHY_APPROVE)
    return {
        "id": case.id,
        "status": case.status,
        "drone_status": case.drone_status,
    }


@router.post("/cases/{case_id}/reject")
def reject_case(
    case_id: int, session: Annotated[Session, Depends(get_session)]
) -> dict:
    case = _get_open_case(session, case_id)
    case.status = CASE_REJECTED
    case.drone_status = DRONE_IDLE
    write_audit(session, case.id, ACTION_REJECT, WHY_REJECT)
    return {
        "id": case.id,
        "status": case.status,
        "drone_status": case.drone_status,
    }
