"""Dump FastAPI OpenAPI JSON for the console orval client (no live server)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from app.main import app

OUT = Path(__file__).resolve().parents[2] / "web" / "openapi.json"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(app.openapi(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
