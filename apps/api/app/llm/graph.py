"""Dispatcher then critic StateGraph. Compile once per worker process (KTD2)."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from app.llm.run_context import AuditDraft, get_run_context
from app.llm.tools import CRITIC_TOOLS, DISPATCHER_TOOLS

DISPATCHER_SYSTEM = """You are the duty-desk dispatcher for a smart-city traffic case.
Use tools to read facts and search playbooks. Then call write_opinion with role
"dispatcher" and a short plain-language recommendation. Propose a drone look only
when the playbook supports it. Never claim you can fly, approve, reject, or close
a road — only a human may do that."""

CRITIC_SYSTEM = """You are the duty-desk critic. Review the dispatcher opinion and
case facts. Use tools if needed, then call write_opinion with role "critic" and a
short critique or confirmation. Never claim you can fly, approve, reject, or close
a road."""


class GraphState(TypedDict):
    messages: Annotated[list, add_messages]


def _truncate(text: str, limit: int = 240) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _message_why(message: AIMessage) -> str:
    if message.tool_calls:
        names = ", ".join(call["name"] for call in message.tool_calls)
        return _truncate(f"tool_calls: {names}")
    content = message.content
    if isinstance(content, list):
        content = " ".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )
    return _truncate(str(content) or "(empty)")


def _has_tool_calls(state: GraphState) -> bool:
    last = state["messages"][-1]
    return bool(getattr(last, "tool_calls", None))


def build_graph(model: BaseChatModel):
    """Build dispatcher → critic with separate tool allowlists per node."""
    dispatcher_model = model.bind_tools(DISPATCHER_TOOLS)
    critic_model = model.bind_tools(CRITIC_TOOLS)
    dispatcher_tools = ToolNode(DISPATCHER_TOOLS)
    critic_tools = ToolNode(CRITIC_TOOLS)

    def dispatcher_node(state: GraphState) -> dict[str, Any]:
        ctx = get_run_context()
        ctx.current_role = "dispatcher"
        messages = [SystemMessage(content=DISPATCHER_SYSTEM), *state["messages"]]
        response = dispatcher_model.invoke(messages)
        ctx.audit_events.append(
            AuditDraft(
                actor="dispatcher",
                action="model_call",
                why=_message_why(response),
            )
        )
        return {"messages": [response]}

    def critic_node(state: GraphState) -> dict[str, Any]:
        ctx = get_run_context()
        ctx.current_role = "critic"
        messages = [SystemMessage(content=CRITIC_SYSTEM), *state["messages"]]
        response = critic_model.invoke(messages)
        ctx.audit_events.append(
            AuditDraft(
                actor="critic",
                action="model_call",
                why=_message_why(response),
            )
        )
        return {"messages": [response]}

    def after_dispatcher(
        state: GraphState,
    ) -> Literal["dispatcher_tools", "critic_entry"]:
        if _has_tool_calls(state):
            return "dispatcher_tools"
        return "critic_entry"

    def after_critic(state: GraphState) -> Literal["critic_tools", "__end__"]:
        if _has_tool_calls(state):
            return "critic_tools"
        return "__end__"

    def critic_entry(state: GraphState) -> dict[str, Any]:
        """Seed the critic turn after the dispatcher finished tool use."""
        ctx = get_run_context()
        prompt = (
            "Dispatcher opinion:\n"
            f"{ctx.dispatcher_opinion or '(none)'}\n\n"
            "Write your critic opinion with the write_opinion tool."
        )
        return {"messages": [HumanMessage(content=prompt)]}

    workflow = StateGraph(GraphState)
    workflow.add_node("dispatcher", dispatcher_node)
    workflow.add_node("dispatcher_tools", dispatcher_tools)
    workflow.add_node("critic_entry", critic_entry)
    workflow.add_node("critic", critic_node)
    workflow.add_node("critic_tools", critic_tools)

    workflow.add_edge(START, "dispatcher")
    workflow.add_conditional_edges(
        "dispatcher",
        after_dispatcher,
        {
            "dispatcher_tools": "dispatcher_tools",
            "critic_entry": "critic_entry",
        },
    )
    workflow.add_edge("dispatcher_tools", "dispatcher")
    workflow.add_edge("critic_entry", "critic")
    workflow.add_conditional_edges(
        "critic",
        after_critic,
        {
            "critic_tools": "critic_tools",
            "__end__": END,
        },
    )
    workflow.add_edge("critic_tools", "critic")
    return workflow.compile()


# Compiled once per process when the worker first needs a live model.
_compiled_graph = None
_compiled_model_id: int | None = None


def get_compiled_graph(model: BaseChatModel):
    """Reuse one compiled graph per process for a given model instance id."""
    global _compiled_graph, _compiled_model_id
    model_id = id(model)
    if _compiled_graph is None or _compiled_model_id != model_id:
        _compiled_graph = build_graph(model)
        _compiled_model_id = model_id
    return _compiled_graph


def reset_compiled_graph() -> None:
    """Test helper: drop the process-level compiled graph."""
    global _compiled_graph, _compiled_model_id
    _compiled_graph = None
    _compiled_model_id = None
