"""Run the opinion graph for one claimed job. Reads only; persist is separate."""

from __future__ import annotations

import contextvars
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import structlog
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
from sqlalchemy.orm import Session

from app.llm.graph import get_compiled_graph
from app.llm.run_context import AuditDraft, RunContext, reset_run_context, set_run_context
from app.models import Case

# Under the job lease (30s). Named tunable, same class as JOB_LEASE_SECONDS.
GRAPH_TIMEOUT_SECONDS = 25.0

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class GraphResult:
    dispatcher_opinion: str | None
    critic_opinion: str | None
    audit_events: tuple[AuditDraft, ...]


def run_opinion_graph(
    session: Session,
    case: Case,
    model: BaseChatModel,
    *,
    timeout_seconds: float = GRAPH_TIMEOUT_SECONDS,
) -> GraphResult:
    """Run dispatcher then critic. On timeout, return empty opinions (KTD5)."""
    log = logger.bind(case_id=case.id, segment=case.segment)
    ctx = RunContext(session=session, case_id=case.id, segment=case.segment)
    token = set_run_context(ctx)
    graph = get_compiled_graph(model)
    initial = {
        "messages": [
            HumanMessage(
                content=(
                    f"Case {case.id} on segment {case.segment}. "
                    f"trigger_kind={case.trigger_kind}. "
                    "Investigate with tools and write a dispatcher opinion."
                )
            )
        ]
    }
    try:
        _invoke_with_timeout(graph, initial, timeout_seconds=timeout_seconds)
    except TimeoutError:
        log.warning("opinion_graph_timeout", timeout_seconds=timeout_seconds)
        return GraphResult(None, None, ())
    finally:
        reset_run_context(token)

    # Both-or-neither for a confident proposal (KTD5 / KTD9).
    if ctx.dispatcher_opinion is None or ctx.critic_opinion is None:
        log.info(
            "opinion_graph_incomplete",
            has_dispatcher=ctx.dispatcher_opinion is not None,
            has_critic=ctx.critic_opinion is not None,
        )
        return GraphResult(None, None, ())
    log.info(
        "opinion_graph_complete",
        audit_events=len(ctx.audit_events),
    )
    return GraphResult(
        ctx.dispatcher_opinion,
        ctx.critic_opinion,
        tuple(ctx.audit_events),
    )


def _invoke_with_timeout(graph, initial: dict, *, timeout_seconds: float) -> None:
    """Run sync graph.invoke under a wall-clock timeout.

    copy_context() so tool ContextVars set on this thread are visible inside the
    worker thread (ThreadPoolExecutor does not inherit contextvars by default).
    """
    copied = contextvars.copy_context()

    def _call() -> None:
        graph.invoke(initial, config={"recursion_limit": 40})

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(copied.run, _call)
        try:
            future.result(timeout=timeout_seconds)
        except TimeoutError:
            future.cancel()
            raise
