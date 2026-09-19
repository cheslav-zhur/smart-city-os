"""Playbook file search for the worker graph (V1-U5 binds this as a tool).

KTD7: case-insensitive substring over filename and body; top 3 chunks;
each chunk max 500 characters. Missing directory or empty hits → [].

Playbooks ship as the top-level `playbooks` package (see pyproject package-data)
so wheels and editable installs resolve the same root: site-packages/playbooks
or apps/api/playbooks.
"""

from __future__ import annotations

import logging
from pathlib import Path

MAX_CHUNK_CHARS = 500
MAX_HITS = 3

logger = logging.getLogger(__name__)

# app/llm/playbook.py → parent package root → sibling `playbooks/` package
DEFAULT_PLAYBOOKS_ROOT = Path(__file__).resolve().parents[2] / "playbooks"


def search_playbook(
    query: str, *, root: Path | None = None
) -> list[str]:
    """Return up to three truncated markdown chunks matching query."""
    playbooks_root = DEFAULT_PLAYBOOKS_ROOT if root is None else root
    if not playbooks_root.is_dir():
        if root is None:
            logger.error(
                "playbooks package missing at %s; search returns []",
                playbooks_root,
            )
        return []

    needle = query.casefold()
    if not needle.strip():
        return []

    hits: list[str] = []
    for path in sorted(playbooks_root.glob("*.md")):
        try:
            body = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        haystack = f"{path.name}\n{body}".casefold()
        if needle not in haystack:
            continue
        hits.append(body[:MAX_CHUNK_CHARS])
        if len(hits) >= MAX_HITS:
            break
    return hits
