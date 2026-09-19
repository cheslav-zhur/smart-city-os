"""Worker graph: dispatcher then critic, allowlist, timeout, fenced persist."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from time import sleep

import pytest
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from sqlalchemy import select

from app.jobs.loop import process_claimed_job
from app.jobs.service import (
    PERSIST_CANCELLED,
    PERSIST_DONE,
    claim_job,
)
from app.llm.graph import reset_compiled_graph
from app.llm.tools import (
    ALL_BOUND_TOOL_NAMES,
    CRITIC_TOOL_NAMES,
    DISPATCHER_TOOL_NAMES,
    FORBIDDEN_TOOL_NAMES,
)
from app.models import AuditEntry, Case, Job
from app.settings import get_settings


def _event(event_id: str, speed: float, seconds: int = 0) -> dict:
    return {
        "event_id": event_id,
        "segment": "A",
        "speed": speed,
        "recorded_at": (
            datetime(2026, 9, 11, 5, 0, tzinfo=UTC) + timedelta(seconds=seconds)
        ).isoformat(),
    }


def _open_collapse(client, prefix: str) -> int:
    client.post("/events", json=_event(f"{prefix}-move", 40.0))
    opened = client.post("/events", json=_event(f"{prefix}-stop", 0.0, seconds=5))
    case_id = opened.json()["case_id"]
    assert case_id is not None
    return case_id


class ScriptedChatModel(FakeMessagesListChatModel):
    """Predetermined AIMessages; bind_tools is a no-op for tests."""

    def bind_tools(self, tools, **kwargs):
        return self


def _happy_scripted_model() -> ScriptedChatModel:
    return ScriptedChatModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "search_playbook",
                        "args": {"query": "crash"},
                        "id": "call_pb",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "write_opinion",
                        "args": {
                            "role": "dispatcher",
                            "text": "Propose a short drone look over segment A.",
                        },
                        "id": "call_disp",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="dispatcher done"),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "write_opinion",
                        "args": {
                            "role": "critic",
                            "text": "Agree: look is optional; human must approve.",
                        },
                        "id": "call_crit",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="critic done"),
        ]
    )


@pytest.fixture(autouse=True)
def _clear_settings_and_graph():
    get_settings.cache_clear()
    reset_compiled_graph()
    yield
    get_settings.cache_clear()
    reset_compiled_graph()


def test_allowlist_excludes_fly_approve_reject() -> None:
    assert FORBIDDEN_TOOL_NAMES.isdisjoint(ALL_BOUND_TOOL_NAMES)
    assert set(DISPATCHER_TOOL_NAMES) == ALL_BOUND_TOOL_NAMES
    assert set(CRITIC_TOOL_NAMES) < ALL_BOUND_TOOL_NAMES
    assert "read_recent_events" not in CRITIC_TOOL_NAMES


def test_stubbed_graph_writes_both_opinions_and_playbook_audit(
    client, db_session, monkeypatch
) -> None:
    monkeypatch.setenv("LLM_API_KEY", "test-stub-key")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "app.llm.chat.make_chat_model",
        lambda settings: _happy_scripted_model(),
    )

    case_id = _open_collapse(client, "agents-happy")
    claimed = claim_job(db_session)
    db_session.commit()
    assert claimed is not None

    status = process_claimed_job(claimed)
    assert status == PERSIST_DONE

    db_session.expire_all()
    case = db_session.get(Case, case_id)
    assert case is not None
    assert case.dispatcher_opinion is not None
    assert "drone look" in case.dispatcher_opinion
    assert case.critic_opinion is not None
    assert "human" in case.critic_opinion.casefold()

    actors = {
        row.actor
        for row in db_session.scalars(
            select(AuditEntry).where(AuditEntry.case_id == case_id)
        )
    }
    assert "dispatcher" in actors
    assert "critic" in actors
    assert "tool:search_playbook" in actors
    assert "tool:write_opinion" in actors


def test_unset_key_skips_graph_opinions_null_case_approvable(
    client, db_session, monkeypatch
) -> None:
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    get_settings.cache_clear()

    case_id = _open_collapse(client, "agents-nokey")
    claimed = claim_job(db_session)
    db_session.commit()
    assert claimed is not None

    status = process_claimed_job(claimed)
    assert status == PERSIST_DONE

    db_session.expire_all()
    case = db_session.get(Case, case_id)
    assert case is not None
    assert case.dispatcher_opinion is None
    assert case.critic_opinion is None
    assert case.status == "open"

    approve = client.post(f"/cases/{case_id}/approve")
    assert approve.status_code == 200


def test_timeout_leaves_opinions_null_and_case_approvable(
    client, db_session, monkeypatch
) -> None:
    monkeypatch.setenv("LLM_API_KEY", "test-stub-key")
    get_settings.cache_clear()

    class SlowModel(ScriptedChatModel):
        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            sleep(0.4)
            return super()._generate(
                messages, stop=stop, run_manager=run_manager, **kwargs
            )

    monkeypatch.setattr(
        "app.llm.chat.make_chat_model",
        lambda settings: SlowModel(responses=[AIMessage(content="never")]),
    )

    import app.llm.run as run_mod

    real_run = run_mod.run_opinion_graph

    def run_with_short_timeout(session, case, model, *, timeout_seconds=0.05):
        return real_run(session, case, model, timeout_seconds=0.05)

    monkeypatch.setattr(run_mod, "run_opinion_graph", run_with_short_timeout)

    case_id = _open_collapse(client, "agents-timeout")
    claimed = claim_job(db_session)
    db_session.commit()
    assert claimed is not None

    status = process_claimed_job(claimed)
    assert status == PERSIST_DONE

    db_session.expire_all()
    case = db_session.get(Case, case_id)
    assert case is not None
    assert case.dispatcher_opinion is None
    assert case.critic_opinion is None
    assert case.status == "open"
    assert client.post(f"/cases/{case_id}/approve").status_code == 200


def test_graph_setup_failure_finishes_empty_opinions(
    client, db_session, monkeypatch
) -> None:
    """Import/model-build errors must hit the empty-opinion fence (review #1)."""
    monkeypatch.setenv("LLM_API_KEY", "test-stub-key")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "app.llm.chat.make_chat_model",
        lambda settings: (_ for _ in ()).throw(RuntimeError("model build failed")),
    )

    case_id = _open_collapse(client, "agents-setup-fail")
    claimed = claim_job(db_session)
    db_session.commit()
    assert claimed is not None

    status = process_claimed_job(claimed)
    assert status == PERSIST_DONE

    db_session.expire_all()
    case = db_session.get(Case, case_id)
    job = db_session.get(Job, claimed.job_id)
    assert case is not None
    assert case.dispatcher_opinion is None
    assert case.critic_opinion is None
    assert case.status == "open"
    assert job is not None
    assert job.status == "done"
    assert client.post(f"/cases/{case_id}/approve").status_code == 200


def test_approved_case_job_does_not_write_opinions(
    client, db_session, monkeypatch
) -> None:
    monkeypatch.setenv("LLM_API_KEY", "test-stub-key")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "app.llm.chat.make_chat_model",
        lambda settings: _happy_scripted_model(),
    )

    case_id = _open_collapse(client, "agents-approved")
    claimed = claim_job(db_session)
    db_session.commit()
    assert claimed is not None

    approve = client.post(f"/cases/{case_id}/approve")
    assert approve.status_code == 200

    status = process_claimed_job(claimed)
    assert status == PERSIST_CANCELLED

    db_session.expire_all()
    case = db_session.get(Case, case_id)
    job = db_session.get(Job, claimed.job_id)
    assert case is not None
    assert case.dispatcher_opinion is None
    assert case.critic_opinion is None
    assert case.status == "approved"
    assert job is not None
    assert job.status == "cancelled"
