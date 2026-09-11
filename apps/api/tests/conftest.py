import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db import SessionLocal
from app.main import app


@pytest.fixture
def client() -> TestClient:
    with SessionLocal() as session:
        session.execute(text("DELETE FROM audit_entries"))
        session.execute(text("DELETE FROM cases"))
        session.execute(text("DELETE FROM events"))
        session.commit()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
