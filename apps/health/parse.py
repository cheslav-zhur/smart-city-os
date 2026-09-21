"""Parse pytest junit XML and vitest JSON into suite + module rows."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from health.modules import FILE_TO_MODULE, MODULE_FILES, MODULE_LAYER


def filename_from_classname(classname: str) -> str:
    last = classname.rsplit(".", 1)[-1]
    if last.endswith(".py"):
        return last
    return f"{last}.py"


def module_for_path(path_or_class: str) -> str | None:
    name = Path(path_or_class.replace("\\", "/")).name
    if name in FILE_TO_MODULE:
        return FILE_TO_MODULE[name]
    if not name.endswith((".py", ".ts", ".tsx")):
        return FILE_TO_MODULE.get(filename_from_classname(path_or_class))
    return None


def empty_suite() -> dict[str, Any]:
    return {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "status": "error",
        "duration_s": 0.0,
    }


def suite_status(total: int, failed: int, *, produced: bool) -> str:
    if not produced:
        return "error"
    if failed > 0:
        return "failed"
    return "passed"


def parse_junit(xml_text: str) -> tuple[dict[str, Any], list[dict[str, str]], list[dict[str, Any]]]:
    """Return (suite, failures, per-case rows with filename)."""
    root = ET.fromstring(xml_text)
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    if not suites and root.tag == "testsuites":
        suites = list(root)

    total = passed = failed = skipped = 0
    duration = 0.0
    failures: list[dict[str, str]] = []
    cases: list[dict[str, Any]] = []

    for suite in suites:
        duration += float(suite.attrib.get("time") or 0)
        for case in suite.findall("testcase"):
            name = case.attrib.get("name") or ""
            classname = case.attrib.get("classname") or ""
            file_attr = case.attrib.get("file") or ""
            filename = Path(file_attr).name if file_attr else filename_from_classname(classname)
            nodeid = f"{classname}::{name}" if classname else name
            fail_el = case.find("failure")
            err_el = case.find("error")
            skip_el = case.find("skipped")
            total += 1
            if skip_el is not None:
                skipped += 1
                outcome = "skipped"
            elif fail_el is not None or err_el is not None:
                failed += 1
                outcome = "failed"
                blob = fail_el if fail_el is not None else err_el
                message = (blob.attrib.get("message") or "").strip()
                if blob is not None and (blob.text or "").strip():
                    message = (message + "\n" + blob.text).strip() if message else blob.text.strip()
                failures.append(
                    {
                        "suite": "",
                        "nodeid": nodeid,
                        "message": message[:2000],
                    }
                )
            else:
                passed += 1
                outcome = "passed"
            cases.append({"filename": filename, "outcome": outcome, "nodeid": nodeid})

    produced = total > 0 or duration > 0 or bool(suites)
    suite = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "status": suite_status(total, failed, produced=produced),
        "duration_s": round(duration, 3),
    }
    return suite, failures, cases


def parse_vitest_json(payload: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]], list[dict[str, Any]]]:
    results = payload.get("testResults")
    if results is None and isinstance(payload.get("data"), dict):
        payload = payload["data"]
        results = payload.get("testResults")

    failures: list[dict[str, str]] = []
    cases: list[dict[str, Any]] = []
    passed = failed = skipped = 0

    if isinstance(results, list):
        for file_result in results:
            filepath = str(file_result.get("name") or file_result.get("filename") or "")
            filename = Path(filepath).name
            assertions = file_result.get("assertionResults") or []
            for assertion in assertions:
                status = str(assertion.get("status") or "")
                title = str(assertion.get("fullName") or assertion.get("title") or "")
                nodeid = f"{filename}::{title}" if filename else title
                if status in {"pending", "skipped", "todo"}:
                    skipped += 1
                    outcome = "skipped"
                elif status == "failed":
                    failed += 1
                    outcome = "failed"
                    messages = assertion.get("failureMessages") or []
                    message = "\n".join(str(m) for m in messages)[:2000]
                    failures.append({"suite": "web", "nodeid": nodeid, "message": message})
                else:
                    passed += 1
                    outcome = "passed"
                cases.append({"filename": filename, "outcome": outcome, "nodeid": nodeid})

    total = passed + failed + skipped
    if total == 0:
        total = int(payload.get("numTotalTests") or 0)
        passed = int(payload.get("numPassedTests") or 0)
        failed = int(payload.get("numFailedTests") or 0)
        skipped = int(payload.get("numPendingTests") or payload.get("numTodoTests") or 0)

    assertion_ms = 0.0
    for file_result in results or []:
        for assertion in file_result.get("assertionResults") or []:
            assertion_ms += float(assertion.get("duration") or 0)
    duration_s = round(assertion_ms / 1000.0, 3)

    produced = total > 0 or bool(results)
    suite = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "status": suite_status(total, failed, produced=produced),
        "duration_s": duration_s,
    }
    return suite, failures, cases


def aggregate_modules(all_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, int]] = {
        module_id: {"tests": 0, "failed": 0} for module_id in MODULE_FILES
    }
    for case in all_cases:
        module_id = module_for_path(case["filename"])
        if module_id is None:
            continue
        buckets[module_id]["tests"] += 1
        if case["outcome"] == "failed":
            buckets[module_id]["failed"] += 1

    modules: list[dict[str, Any]] = []
    for module_id in MODULE_FILES:
        row = buckets[module_id]
        modules.append(
            {
                "id": module_id,
                "layer": MODULE_LAYER[module_id],
                "tests": row["tests"],
                "failed": row["failed"],
                "status": "failed" if row["failed"] else "passed",
            }
        )
    return modules
