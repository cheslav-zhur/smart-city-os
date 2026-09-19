from sqlalchemy.orm import Session

from app.models import AuditEntry
from app.settings import get_settings

ACTION_APPROVE = "approve"
ACTION_REJECT = "reject"
WHY_APPROVE = "approved send drone"
WHY_REJECT = "rejected send drone"


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
