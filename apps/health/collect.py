"""Run pytest / vitest / tsc and write .local/health/ (gitignored)."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from health.parse import aggregate_modules, empty_suite, parse_junit, parse_vitest_json
from health.render import build_quality, render_html


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def health_dir(root: Path) -> Path:
    return root / ".local" / "health"


def git_meta(root: Path) -> dict[str, Any]:
    def _git(args: list[str]) -> str:
        proc = subprocess.run(
            args,
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        return proc.stdout.strip() if proc.returncode == 0 else ""

    sha = _git(["git", "rev-parse", "--short=7", "HEAD"])
    branch = _git(["git", "branch", "--show-current"]) or _git(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"]
    )
    dirty = bool(_git(["git", "status", "--porcelain"]))
    return {"sha": sha or "unknown", "branch": branch or "HEAD", "dirty": dirty}


def _run(cmd: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> int:
    print("+", " ".join(cmd), f"(cwd={cwd})", flush=True)
    proc = subprocess.run(cmd, cwd=cwd, env=env)
    return proc.returncode


def load_text(path: Path) -> str | None:
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def run_report(root: Path) -> dict[str, Any]:
    out = health_dir(root)
    out.mkdir(parents=True, exist_ok=True)
    venv_pytest = root / "apps" / "api" / ".venv" / "bin" / "pytest"
    if not venv_pytest.is_file():
        raise SystemExit(
            "apps/api/.venv is missing pytest. "
            "From apps/api: python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'"
        )

    api_xml = out / "api-junit.xml"
    sim_xml = out / "sim-junit.xml"
    web_json_path = out / "web-vitest.json"

    env = os.environ.copy()
    api_code = _run(
        [str(venv_pytest), f"--junitxml={api_xml}"],
        cwd=root / "apps" / "api",
        env=env,
    )
    sim_code = _run(
        [str(venv_pytest), f"--junitxml={sim_xml}"],
        cwd=root / "apps" / "sim",
        env=env,
    )
    web_code = _run(
        [
            "pnpm",
            "exec",
            "vitest",
            "run",
            "--reporter=default",
            "--reporter=json",
            f"--outputFile={web_json_path}",
        ],
        cwd=root / "apps" / "web",
        env=env,
    )
    tsc_code = _run(
        ["pnpm", "exec", "tsc", "-b", "--pretty", "false"],
        cwd=root / "apps" / "web",
        env=env,
    )

    all_cases: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    suites: dict[str, dict[str, Any]] = {}

    api_text = load_text(api_xml)
    if api_text:
        suite, fails, cases = parse_junit(api_text)
        for item in fails:
            item["suite"] = "api"
        suites["api"] = suite
        failures.extend(fails)
        all_cases.extend(cases)
        if api_code != 0 and suite["failed"] == 0 and suite["status"] == "passed":
            suite["status"] = "error"
    else:
        suites["api"] = empty_suite()

    sim_text = load_text(sim_xml)
    if sim_text:
        suite, fails, cases = parse_junit(sim_text)
        for item in fails:
            item["suite"] = "sim"
        suites["sim"] = suite
        failures.extend(fails)
        all_cases.extend(cases)
        if sim_code != 0 and suite["failed"] == 0 and suite["status"] == "passed":
            suite["status"] = "error"
    else:
        suites["sim"] = empty_suite()

    web_raw = load_text(web_json_path)
    if web_raw:
        try:
            payload = json.loads(web_raw)
        except json.JSONDecodeError:
            payload = {}
        suite, fails, cases = parse_vitest_json(payload if isinstance(payload, dict) else {})
        suites["web"] = suite
        failures.extend(fails)
        all_cases.extend(cases)
        if web_code != 0 and suite["failed"] == 0:
            suite["status"] = "error"
    else:
        suites["web"] = empty_suite()

    tsc_status = "passed" if tsc_code == 0 else "failed"

    checks = {
        "api_pytest": suites["api"]["status"] if suites["api"]["status"] != "error" else "error",
        "sim_pytest": suites["sim"]["status"] if suites["sim"]["status"] != "error" else "error",
        "web_vitest": suites["web"]["status"] if suites["web"]["status"] != "error" else "error",
        "web_tsc": tsc_status,
        "web_in_ci": "missing",
    }
    if api_code != 0 and checks["api_pytest"] == "passed":
        checks["api_pytest"] = "failed"
    if sim_code != 0 and checks["sim_pytest"] == "passed":
        checks["sim_pytest"] = "failed"
    if web_code != 0 and checks["web_vitest"] == "passed":
        checks["web_vitest"] = "failed"

    generated_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    quality = build_quality(
        generated_at=generated_at,
        git=git_meta(root),
        suites=suites,
        checks=checks,
        modules=aggregate_modules(all_cases),
        failures=failures,
    )
    (out / "quality.json").write_text(
        json.dumps(quality, indent=2) + "\n", encoding="utf-8"
    )
    html_path = out / "index.html"
    html_path.write_text(render_html(quality), encoding="utf-8")
    print(f"Wrote {html_path}", flush=True)
    return quality


def main() -> int:
    run_report(repo_root())
    return 0
