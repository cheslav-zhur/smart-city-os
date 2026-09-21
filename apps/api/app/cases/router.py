from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.audit.service import list_audit_for_case
from app.cases.schemas import AuditListItem, CaseDecisionOut, CaseListItem
from app.cases.service import (
    CaseAlreadyDecidedError,
    CaseNotFoundError,
    approve_case,
    get_case,
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
            dispatcher_opinion=case.dispatcher_opinion,
            critic_opinion=case.critic_opinion,
        )
        for case in list_cases(session)
    ]


@router.get("/cases/{case_id}/audit")
def get_case_audit(
    case_id: int, session: Annotated[Session, Depends(get_session)]
) -> list[AuditListItem]:
    if get_case(session, case_id) is None:
        raise HTTPException(status_code=404, detail="case not found")
    return [
        AuditListItem(
            id=entry.id,
            actor=entry.actor,
            action=entry.action,
            why=entry.why,
            created_at=entry.created_at,
        )
        for entry in list_audit_for_case(session, case_id)
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
