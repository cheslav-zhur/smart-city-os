"""Worker poll loop. Claim and persist are separate short transactions."""

import time

from app.db import SessionLocal
from app.jobs.service import ClaimedJob, claim_job, finish_stub_job

JOB_POLL_SECONDS = 1.0


def claim_next_job() -> ClaimedJob | None:
    with SessionLocal() as session:
        claimed = claim_job(session)
        session.commit()
        return claimed


def run_worker(*, poll_seconds: float = JOB_POLL_SECONDS) -> None:
    """Claim forever. KeyboardInterrupt is the shutdown path for `python -m`."""
    while True:
        claimed = claim_next_job()
        if claimed is None:
            time.sleep(poll_seconds)
            continue
        with SessionLocal() as session:
            finish_stub_job(session, claimed)
            session.commit()
