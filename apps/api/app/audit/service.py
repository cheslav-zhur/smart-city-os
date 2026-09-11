from sqlalchemy.orm import Session

from app.models import AuditEntry
from app.settings import get_settings

ACTION_APPROVE = "approve"
ACTION_REJECT = "reject"
WHY_APPROVE = "approved send drone"
WHY_REJECT = "rejected send drone"


def write_audit(session: Session, case_id: int, action: str, why: str) -> AuditEntry:
    entry = AuditEntry(
        case_id=case_id,
        actor=get_settings().audit_actor,
        action=action,
        why=why,
    )
    session.add(entry)
    session.flush()
    return entry
