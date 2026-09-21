"""Fill template.html with a quality snapshot. Does not run tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STALE_AFTER_HOURS = 24
TEMPLATE_PATH = Path(__file__).with_name("template.html")


def build_quality(
    *,
    generated_at: str,
    git: dict[str, Any],
    suites: dict[str, dict[str, Any]],
    checks: dict[str, str],
    modules: list[dict[str, Any]],
    failures: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "git": git,
        "suites": suites,
        "checks": checks,
        "modules": modules,
        "failures": failures,
    }


def load_template() -> str:
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def render_html(quality: dict[str, Any]) -> str:
    payload = json.dumps(quality, indent=2).replace("<", "\\u003c")
    template = load_template()
    if "__QUALITY_JSON__" not in template or "__STALE_HOURS__" not in template:
        raise RuntimeError(
            f"{TEMPLATE_PATH.name} is missing __QUALITY_JSON__ or __STALE_HOURS__"
        )
    return template.replace("__STALE_HOURS__", str(STALE_AFTER_HOURS)).replace(
        "__QUALITY_JSON__", payload
    )
