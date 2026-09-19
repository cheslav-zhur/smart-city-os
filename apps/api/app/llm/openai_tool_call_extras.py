"""Preserve non-OpenAI tool_call fields through ChatOpenAI converters.

Gemini 3's OpenAI-compatible endpoint returns
``tool_calls[].extra_content.google.thought_signature`` and requires the same
field on the next turn. ``langchain-openai`` 1.6.2 drops those keys; without
them the second tool-turn 400s. Upstream fix (PR #37356) is not in 1.6.2 yet —
this shim mirrors that side-channel until we can bump the pin.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage
from langchain_openai.chat_models import base as openai_base

_OPENAI_TOOL_CALL_EXTRAS_KEY = "__openai_tool_call_extras__"
_RESERVED_TOOL_CALL_KEYS = frozenset({"id", "type", "function", "index"})

_installed = False
_original_dict_to_message = openai_base._convert_dict_to_message
_original_message_to_dict = openai_base._convert_message_to_dict


def _capture_tool_call_extras(
    raw_tool_call: Mapping[str, Any],
    *,
    fallback_key: str | None = None,
) -> tuple[str | None, dict[str, Any]]:
    extras = {
        key: value
        for key, value in raw_tool_call.items()
        if key not in _RESERVED_TOOL_CALL_KEYS
    }
    if not extras:
        return None, {}
    key = raw_tool_call.get("id") or fallback_key
    return key, extras


def _convert_dict_to_message_with_extras(_dict: Mapping[str, Any]) -> BaseMessage:
    message = _original_dict_to_message(_dict)
    if not isinstance(message, AIMessage):
        return message
    raw_tool_calls = _dict.get("tool_calls") or []
    tool_call_extras: dict[str, dict[str, Any]] = {}
    for raw_tool_call in raw_tool_calls:
        key, extras = _capture_tool_call_extras(raw_tool_call)
        if key and extras:
            tool_call_extras[key] = extras
    if not tool_call_extras:
        return message
    additional_kwargs = {
        **message.additional_kwargs,
        _OPENAI_TOOL_CALL_EXTRAS_KEY: tool_call_extras,
    }
    return message.model_copy(update={"additional_kwargs": additional_kwargs})


def _reconcile_extras_placeholders(
    message: AIMessage,
    extras_map: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    reconciled = dict(extras_map)
    for index, tool_call in enumerate(message.tool_calls):
        placeholder = f"__index_{index}"
        tool_call_id = tool_call.get("id")
        if placeholder in reconciled and tool_call_id and tool_call_id not in reconciled:
            reconciled[tool_call_id] = reconciled.pop(placeholder)
    return reconciled


def _convert_message_to_dict_with_extras(
    message: BaseMessage,
    api: str = "chat/completions",
) -> dict:
    message_dict = _original_message_to_dict(message, api=api)  # type: ignore[arg-type]
    if not isinstance(message, AIMessage):
        return message_dict
    # Only merge when typed tool_calls drove serialization (upstream escape-hatch
    # path strips extras on purpose).
    if not (message.tool_calls or message.invalid_tool_calls):
        return message_dict
    raw_extras = message.additional_kwargs.get(_OPENAI_TOOL_CALL_EXTRAS_KEY) or {}
    if not raw_extras or not message_dict.get("tool_calls"):
        return message_dict
    extras_map = _reconcile_extras_placeholders(message, dict(raw_extras))
    for out_tool_call in message_dict["tool_calls"]:
        tool_call_id = out_tool_call.get("id")
        if tool_call_id and tool_call_id in extras_map:
            out_tool_call.update(extras_map[tool_call_id])
    return message_dict


def install_tool_call_extras_shim() -> None:
    """Patch ChatOpenAI converters once per process. Idempotent."""
    global _installed
    if _installed:
        return
    openai_base._convert_dict_to_message = _convert_dict_to_message_with_extras
    openai_base._convert_message_to_dict = _convert_message_to_dict_with_extras
    _installed = True
