"""Round-trip Gemini tool_call extra_content through ChatOpenAI converters."""

from __future__ import annotations

from langchain_core.messages import AIMessage
from langchain_core.messages.tool import ToolCall
from langchain_openai.chat_models import base as openai_base

from app.llm.openai_tool_call_extras import (
    _OPENAI_TOOL_CALL_EXTRAS_KEY,
    install_tool_call_extras_shim,
)


def test_tool_call_extras_round_trip() -> None:
    install_tool_call_extras_shim()
    raw_tool_call = {
        "id": "call_abc",
        "type": "function",
        "function": {"name": "read_case", "arguments": "{}"},
        "extra_content": {"google": {"thought_signature": "SIG=="}},
    }
    message = openai_base._convert_dict_to_message(
        {"role": "assistant", "content": None, "tool_calls": [raw_tool_call]}
    )
    assert isinstance(message, AIMessage)
    assert message.tool_calls[0]["id"] == "call_abc"
    assert message.additional_kwargs[_OPENAI_TOOL_CALL_EXTRAS_KEY] == {
        "call_abc": {"extra_content": {"google": {"thought_signature": "SIG=="}}}
    }

    out = openai_base._convert_message_to_dict(message)
    assert out["tool_calls"][0]["extra_content"] == {
        "google": {"thought_signature": "SIG=="}
    }
    assert out["tool_calls"][0]["function"] == {
        "name": "read_case",
        "arguments": "{}",
    }


def test_tool_call_without_extras_unchanged() -> None:
    install_tool_call_extras_shim()
    message = AIMessage(
        content="",
        tool_calls=[
            ToolCall(name="read_case", args={}, id="x", type="tool_call"),
        ],
    )
    out = openai_base._convert_message_to_dict(message)
    assert out["tool_calls"] == [
        {
            "type": "function",
            "id": "x",
            "function": {"name": "read_case", "arguments": "{}"},
        }
    ]
