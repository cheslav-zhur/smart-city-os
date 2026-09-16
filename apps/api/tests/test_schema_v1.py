"""Schema contract for v1 kinds, jobs, and opinions. Does not open cases by rule."""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import func, inspect, select, text
from sqlalchemy.exc import IntegrityError

from app.db import SessionLocal, engine
from app.models import JOB_DONE, JOB_PENDING, Case, Event, Job

API_ROOT = Path(__file__).resolve().parents[1]


def _alembic_config() -> Config:
    cfg = Config(str(API_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(API_ROOT / "alembic"))
    # Alembic warns if this is missing when Config is built in-process.
    cfg.set_main_option("path_separator", "os")
    return cfg


def test_v1_columns_exist_and_one_job_inserts(client, db_session) -> None:
    columns = {
        table: {col["name"] for col in inspect(engine).get_columns(table)}
        for table in ("events", "cases", "jobs")
    }

    assert "kind" in columns["events"]
    assert {
        "trigger_kind",
        "dispatcher_opinion",
        "critic_opinion",
        "rationale",
    } <= columns["cases"]
    assert {
        "case_id",
        "status",
        "lease_version",
        "attempts",
        "lease_expires_at",
    } <= columns["jobs"]

    case = Case(segment="A", status="open", drone_status="idle", rationale="kept")
    db_session.add(case)
    db_session.flush()
    db_session.add(Job(case_id=case.id, status=JOB_PENDING))
    db_session.commit()

    stored = db_session.get(Case, case.id)
    assert stored is not None
    assert stored.rationale == "kept"
    assert db_session.scalar(select(func.count()).select_from(Job)) == 1


def test_pre_0003_row_migrates_without_a_job(client) -> None:
    """Old tape rows get kind=crash_drop; we do not invent a job for them."""
    engine.dispose()
    cfg = _alembic_config()
    command.downgrade(cfg, "0002_case_rationale")
    try:
        with engine.connect() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO events (event_id, segment, speed, recorded_at)
                    VALUES ('pre-0003', 'A', 12.0, NOW())
                    """
                )
            )
            connection.execute(
                text(
                    """
                    INSERT INTO cases (segment, status, drone_status, rationale)
                    VALUES ('A', 'open', 'idle', 'old why')
                    """
                )
            )
            connection.commit()
        command.upgrade(cfg, "head")
        with SessionLocal() as session:
            event = session.scalar(select(Event).where(Event.event_id == "pre-0003"))
            case = session.scalar(select(Case))
            assert event is not None
            assert event.kind == "crash_drop"
            assert case is not None
            assert case.trigger_kind is None
            assert case.rationale == "old why"
            assert session.scalar(select(func.count()).select_from(Job)) == 0
    finally:
        command.upgrade(cfg, "head")
        engine.dispose()


def test_second_job_for_same_case_rejected_after_done(client, db_session) -> None:
    case = Case(segment="A", status="open", drone_status="idle")
    db_session.add(case)
    db_session.flush()
    db_session.add(Job(case_id=case.id, status=JOB_PENDING))
    db_session.flush()
    job = db_session.scalar(select(Job).where(Job.case_id == case.id))
    assert job is not None
    job.status = JOB_DONE
    db_session.flush()

    db_session.add(Job(case_id=case.id, status=JOB_PENDING))
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_two_open_cases_on_one_segment_rejected(client, db_session) -> None:
    db_session.add(Case(segment="A", status="open", drone_status="idle"))
    db_session.flush()
    db_session.add(Case(segment="A", status="open", drone_status="idle"))
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_job_missing_case_fk_fails(client, db_session) -> None:
    db_session.add(Job(case_id=999_999, status=JOB_PENDING))
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()
