"""OpenAI-compatible chat client (Gemini AI Studio via base_url, or any compatible host)."""

from __future__ import annotations

from langchain_openai import ChatOpenAI

from app.settings import Settings

# Starter demo model for Google AI Studio OpenAI-compatible endpoint.
DEFAULT_LLM_MODEL = "gemini-3.6-flash"
DEFAULT_LLM_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


def make_chat_model(settings: Settings) -> ChatOpenAI:
    """Build the runtime chat model. Caller must ensure llm_api_key is set."""
    if not settings.llm_api_key:
        raise ValueError("llm_api_key is required to build the chat model")
    return ChatOpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url or DEFAULT_LLM_BASE_URL,
        model=settings.llm_model or DEFAULT_LLM_MODEL,
        temperature=0,
    )
