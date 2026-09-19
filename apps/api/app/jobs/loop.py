"""Worker poll loop. Claim, optional graph, and persist are separate short txns."""

from __future__ import annotations

import logging
import time

from app.db import SessionLocal
from app.jobs.service import (
    AuditPersistRow,
    ClaimedJob,
    claim_job,
    finish_empty_opinions,
    persist_job_result,
)
from app.models import Case
from app.settings import get_settings

JOB_POLL_SECONDS = 1.0

logger = logging.getLogger(__name__)


def claim_next_job() -> ClaimedJob | None:
    with SessionLocal() as session:
        claimed = claim_job(session)
        session.commit()
        return claimed


def process_claimed_job(claimed: ClaimedJob) -> str:
    """Run the opinion path for one claim. Returns persist outcome string."""
    settings = get_settings()
    if not settings.llm_api_key:
        with SessionLocal() as session:
            status = finish_empty_opinions(session, claimed)
            session.commit()
            return status

    result = None
    try:
        # Import graph only on the worker path with a key (KTD12: API stays free of it).
        from app.llm.chat import make_chat_model
        from app.llm.run import run_opinion_graph

        model = make_chat_model(settings)
        with SessionLocal() as session:
            case = session.get(Case, claimed.case_id)
            if case is None:
                status = finish_empty_opinions(session, claimed)
                session.commit()
                return status
            try:
                result = run_opinion_graph(session, case, model)
            finally:
                # Tools are read-only against the DB; drop the read session cleanly.
                session.rollback()
    except Exception:
        # Import, model build, or provider failures must not leave the lease stuck.
        logger.exception(
            "opinion graph failed; finishing empty opinions job_id=%s case_id=%s "
            "lease_version=%s",
            claimed.job_id,
            claimed.case_id,
            claimed.lease_version,
        )
        result = None

    with SessionLocal() as session:
        if result is None:
            status = finish_empty_opinions(session, claimed)
        else:
            audit_rows = tuple(
                AuditPersistRow(actor=e.actor, action=e.action, why=e.why)
                for e in result.audit_events
            )
            status = persist_job_result(
                session,
                job_id=claimed.job_id,
                lease_version=claimed.lease_version,
                dispatcher_opinion=result.dispatcher_opinion,
                critic_opinion=result.critic_opinion,
                audit_rows=audit_rows,
            )
        session.commit()
        return status


def run_worker(*, poll_seconds: float = JOB_POLL_SECONDS) -> None:
    """Claim forever. KeyboardInterrupt is the shutdown path for `python -m`."""
    while True:
        claimed = claim_next_job()
        if claimed is None:
            time.sleep(poll_seconds)
            continue
        try:
            process_claimed_job(claimed)
        except Exception:
            # Last resort: one bad job must not kill the poll loop.
            logger.exception(
                "process_claimed_job crashed job_id=%s case_id=%s",
                claimed.job_id,
                claimed.case_id,
            )
