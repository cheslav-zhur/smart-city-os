from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.cases.schemas import CaseDecisionOut, CaseListItem
from app.cases.service import (
    CaseAlreadyDecidedError,
    CaseNotFoundError,
    approve_case,
    list_cases,
    reject_case,
)
from app.db import get_session
from app.models import Case

router = APIRouter(tags=["cases"])


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
    case = _decide(approve_case, session, case_id)
    return CaseDecisionOut(
        id=case.id,
        status=case.status,
        drone_status=case.drone_status,
    )


@router.post("/cases/{case_id}/reject")
def post_reject(
    case_id: int, session: Annotated[Session, Depends(get_session)]
) -> CaseDecisionOut:
    case = _decide(reject_case, session, case_id)
    return CaseDecisionOut(
        id=case.id,
        status=case.status,
        drone_status=case.drone_status,
    )


def _decide(
    fn: Callable[[Session, int], Case], session: Session, case_id: int
) -> Case:
    try:
        return fn(session, case_id)
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail="case not found") from exc
    except CaseAlreadyDecidedError as exc:
        raise HTTPException(status_code=409, detail="case already decided") from exc
