"""Allowlisted graph tools. Bound names are the allowlist — no fly/approve/reject."""

from __future__ import annotations

import json

from langchain_core.tools import tool

from app.llm.playbook import search_playbook as search_playbook_files
from app.llm.run_context import AuditDraft, get_run_context
from app.llm.service import read_recent_events
from app.models import Case

# Names the model may call. AE7: fly / approve / reject / close_road stay absent.
DISPATCHER_TOOL_NAMES = (
    "read_recent_events",
    "read_case",
    "search_playbook",
    "write_opinion",
)
CRITIC_TOOL_NAMES = (
    "read_case",
    "search_playbook",
    "write_opinion",
)
FORBIDDEN_TOOL_NAMES = frozenset(
    {"fly", "approve", "reject", "close_road", "close-road"}
)


def _audit_tool(name: str, why: str) -> None:
    get_run_context().audit_events.append(
        AuditDraft(actor=f"tool:{name}", action="tool_call", why=why)
    )


@tool("read_recent_events")
def read_recent_events_tool(limit: int = 5) -> str:
    """Read the newest speed samples for this case's segment."""
    ctx = get_run_context()
    events = read_recent_events(ctx.session, ctx.segment, limit=limit)
    payload = [
        {
            "kind": event.kind,
            "speed": event.speed,
            "recorded_at": event.recorded_at.isoformat(),
        }
        for event in events
    ]
    _audit_tool("read_recent_events", f"limit={limit}; count={len(payload)}")
    return json.dumps(payload)


@tool("read_case")
def read_case_tool() -> str:
    """Read the open case card fields (segment, trigger, opinions so far)."""
    ctx = get_run_context()
    case = ctx.session.get(Case, ctx.case_id)
    if case is None:
        _audit_tool("read_case", "missing")
        return json.dumps({"error": "case not found"})
    payload = {
        "id": case.id,
        "segment": case.segment,
        "status": case.status,
        "trigger_kind": case.trigger_kind,
        "dispatcher_opinion": ctx.dispatcher_opinion,
        "critic_opinion": ctx.critic_opinion,
    }
    _audit_tool("read_case", f"case_id={case.id}")
    return json.dumps(payload)


@tool("search_playbook")
def search_playbook_tool(query: str) -> str:
    """Search markdown playbooks by case-insensitive substring (filename + body)."""
    hits = search_playbook_files(query)
    _audit_tool("search_playbook", f"query={query!r}; hits={len(hits)}")
    return json.dumps(hits)


@tool("write_opinion")
def write_opinion_tool(role: str, text: str) -> str:
    """Write this role's opinion into graph memory (not the database)."""
    ctx = get_run_context()
    role_norm = role.strip().casefold()
    if role_norm not in {"dispatcher", "critic"}:
        _audit_tool("write_opinion", f"rejected role={role!r}")
        return "rejected: role must be dispatcher or critic"
    if role_norm != ctx.current_role:
        _audit_tool(
            "write_opinion",
            f"rejected role={role_norm} current={ctx.current_role}",
        )
        return f"rejected: current role is {ctx.current_role}"
    text_clean = text.strip()
    if not text_clean:
        _audit_tool("write_opinion", "rejected empty text")
        return "rejected: empty opinion"
    if role_norm == "dispatcher":
        ctx.dispatcher_opinion = text_clean
    else:
        ctx.critic_opinion = text_clean
    _audit_tool("write_opinion", f"role={role_norm}; chars={len(text_clean)}")
    return "ok"


DISPATCHER_TOOLS = [
    read_recent_events_tool,
    read_case_tool,
    search_playbook_tool,
    write_opinion_tool,
]
CRITIC_TOOLS = [
    read_case_tool,
    search_playbook_tool,
    write_opinion_tool,
]

ALL_BOUND_TOOL_NAMES = frozenset(tool.name for tool in DISPATCHER_TOOLS)
