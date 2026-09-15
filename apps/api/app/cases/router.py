from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.cases.schemas import CaseDecisionOut, CaseListItem
from app.cases.service import (
    CASE_OPEN,
    approve_case,
    list_cases,
    reject_case,
)
from app.db import get_session
from app.models import Case

router = APIRouter()


def _get_open_case(session: Session, case_id: int) -> Case:
    case = session.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="case not found")
    if case.status != CASE_OPEN:
        raise HTTPException(status_code=409, detail="case already decided")
    return case


@router.get("/cases")
def get_cases(
    session: Annotated[Session, Depends(get_session)],
) -> list[CaseListItem]:
    return [
        CaseListItem(
            id=case.id,
            segment=case.segment,
            status=case.status,
            drone_status=case.drone_status,
            rationale=case.rationale,
        )
        for case in list_cases(session)
    ]


@router.post("/cases/{case_id}/approve")
def post_approve(
    case_id: int, session: Annotated[Session, Depends(get_session)]
) -> CaseDecisionOut:
    case = approve_case(session, _get_open_case(session, case_id))
    return CaseDecisionOut(
        id=case.id,
        status=case.status,
        drone_status=case.drone_status,
    )


@router.post("/cases/{case_id}/reject")
def post_reject(
    case_id: int, session: Annotated[Session, Depends(get_session)]
) -> CaseDecisionOut:
    case = reject_case(session, _get_open_case(session, case_id))
    return CaseDecisionOut(
        id=case.id,
        status=case.status,
        drone_status=case.drone_status,
    )
