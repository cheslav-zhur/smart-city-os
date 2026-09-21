from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditEntry
from app.settings import get_settings

ACTION_APPROVE = "approve"
ACTION_REJECT = "reject"
ACTION_OUTDATED = "outdated"
ACTOR_SYSTEM = "system"
WHY_APPROVE = "approved send drone"
WHY_REJECT = "rejected send drone"
WHY_OUTDATED = "displaced by a newer incident"


def list_audit_for_case(session: Session, case_id: int) -> list[AuditEntry]:
    """Append-only audit rows for a case, oldest first."""
    return list(
        session.scalars(
            select(AuditEntry)
            .where(AuditEntry.case_id == case_id)
            .order_by(AuditEntry.id.asc())
        ).all()
    )


def write_audit(session: Session, case_id: int, action: str, why: str) -> AuditEntry:
    """Operator audit row (actor from settings)."""
    return write_audit_entry(
        session,
        case_id=case_id,
        actor=get_settings().audit_actor,
        action=action,
        why=why,
    )


def write_audit_entry(
    session: Session,
    *,
    case_id: int,
    actor: str,
    action: str,
    why: str,
) -> AuditEntry:
    """Append one audit row with an explicit actor (operator or model/tool)."""
    entry = AuditEntry(
        case_id=case_id,
        actor=actor,
        action=action,
        why=why,
    )
    session.add(entry)
    session.flush()
    return entry
