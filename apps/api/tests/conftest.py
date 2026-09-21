"""API tests use city_test so truncate/downgrade cannot wipe the desk."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url


def pytest_configure(config: pytest.Config) -> None:
    raw = os.environ.get("DATABASE_URL")
    if not raw:
        raise pytest.UsageError("DATABASE_URL is unset.")
    url = make_url(raw)
    if url.database == "city":
        os.environ["DATABASE_URL"] = url.set(database="city_test").render_as_string(
            hide_password=False
        )
    elif url.database != "city_test":
        raise pytest.UsageError(
            f"API tests expect database city or city_test, got {url.database!r}."
        )
    _ensure_city_test(os.environ["DATABASE_URL"])
    from alembic import command
    from alembic.config import Config

    from app.settings import get_settings

    get_settings.cache_clear()
    api_root = Path(__file__).resolve().parents[1]
    cfg = Config(str(api_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(api_root / "alembic"))
    cfg.set_main_option("path_separator", "os")
    command.upgrade(cfg, "head")


def _ensure_city_test(url_str: str) -> None:
    sa = (
        url_str.replace("postgresql://", "postgresql+psycopg://", 1)
        if url_str.startswith("postgresql://")
        else url_str
    )
    engine = create_engine(
        make_url(sa).set(database="postgres").render_as_string(hide_password=False),
        isolation_level="AUTOCOMMIT",
    )
    try:
        with engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = 'city_test'")
            ).scalar()
            if not exists:
                conn.execute(text("CREATE DATABASE city_test"))
    finally:
        engine.dispose()


@pytest.fixture
def client() -> TestClient:
    from app.db import SessionLocal
    from app.main import app

    with SessionLocal() as session:
        session.execute(text("DELETE FROM jobs"))
        session.execute(text("DELETE FROM audit_entries"))
        session.execute(text("DELETE FROM cases"))
        session.execute(text("DELETE FROM events"))
        session.commit()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session():
    from app.db import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
