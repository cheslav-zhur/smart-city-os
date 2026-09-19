"""Per-job run bag for graph tools. Opinions stay in memory until fenced persist."""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass, field

from sqlalchemy.orm import Session


@dataclass
class AuditDraft:
    actor: str
    action: str
    why: str


@dataclass
class RunContext:
    session: Session
    case_id: int
    segment: str
    current_role: str = "dispatcher"
    dispatcher_opinion: str | None = None
    critic_opinion: str | None = None
    audit_events: list[AuditDraft] = field(default_factory=list)


_run_ctx: ContextVar[RunContext | None] = ContextVar("llm_run_ctx", default=None)


def get_run_context() -> RunContext:
    ctx = _run_ctx.get()
    if ctx is None:
        raise RuntimeError("LLM run context is not set")
    return ctx


def set_run_context(ctx: RunContext | None):
    return _run_ctx.set(ctx)


def reset_run_context(token) -> None:
    _run_ctx.reset(token)
