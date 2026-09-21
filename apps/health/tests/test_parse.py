"""Parser tests for apps/health (no Postgres)."""

from __future__ import annotations

import json
import unittest

from health.parse import aggregate_modules, parse_junit, parse_vitest_json
from health.render import TEMPLATE_PATH, build_quality, load_template, render_html

JUNIT = """\
<?xml version="1.0" encoding="utf-8"?>
<testsuites>
  <testsuite name="pytest" errors="0" failures="1" skipped="1" tests="4" time="1.5">
    <testcase classname="tests.test_ingest" name="test_duplicate" time="0.1"/>
    <testcase classname="tests.test_event_kinds" name="test_jam" time="0.2"/>
    <testcase classname="tests.test_hitl" name="test_404" time="0.05">
      <failure message="assert 200 == 404">AssertionError</failure>
    </testcase>
    <testcase classname="tests.test_mystery" name="test_unmapped" time="0.01">
      <skipped message="not yet"/>
    </testcase>
  </testsuite>
</testsuites>
"""

VITEST = {
    "numTotalTests": 3,
    "numPassedTests": 2,
    "numFailedTests": 1,
    "numPendingTests": 0,
    "testResults": [
        {
            "name": "/workspace/apps/web/src/features/cases/CaseCard/CaseCard.test.tsx",
            "assertionResults": [
                {
                    "fullName": "Send drone posts approve",
                    "status": "passed",
                    "duration": 12,
                    "failureMessages": [],
                },
                {
                    "fullName": "Dismiss posts reject",
                    "status": "failed",
                    "duration": 8,
                    "failureMessages": ["expected 200"],
                },
            ],
        },
        {
            "name": "/workspace/apps/web/src/shared/lib/time.test.ts",
            "assertionResults": [
                {
                    "fullName": "formats recent seconds",
                    "status": "passed",
                    "duration": 1,
                    "failureMessages": [],
                }
            ],
        },
    ],
}


class HealthReportTests(unittest.TestCase):
    def test_junit_counts_and_module_map(self) -> None:
        suite, failures, cases = parse_junit(JUNIT)
        self.assertEqual(suite["total"], 4)
        self.assertEqual(suite["passed"], 2)
        self.assertEqual(suite["failed"], 1)
        self.assertEqual(suite["skipped"], 1)
        self.assertEqual(suite["status"], "failed")
        self.assertEqual(len(failures), 1)
        self.assertIn("test_404", failures[0]["nodeid"])

        modules = {row["id"]: row for row in aggregate_modules(cases)}
        self.assertEqual(modules["api.events"]["tests"], 2)
        self.assertEqual(modules["api.cases"]["tests"], 1)
        self.assertEqual(modules["api.cases"]["failed"], 1)
        self.assertEqual(modules["api.cases"]["status"], "failed")
        mapped = sum(row["tests"] for row in modules.values())
        self.assertEqual(mapped, 3)
        self.assertEqual(suite["total"] - mapped, 1)

    def test_vitest_maps_card_and_shared(self) -> None:
        suite, failures, cases = parse_vitest_json(VITEST)
        self.assertEqual(suite["total"], 3)
        self.assertEqual(suite["failed"], 1)
        self.assertEqual(len(failures), 1)
        modules = {row["id"]: row for row in aggregate_modules(cases)}
        self.assertEqual(modules["web.cases"]["tests"], 2)
        self.assertEqual(modules["web.cases"]["failed"], 1)
        self.assertEqual(modules["web.shared"]["tests"], 1)

    def test_html_comes_from_template_file(self) -> None:
        self.assertTrue(TEMPLATE_PATH.is_file())
        raw = load_template()
        self.assertIn("__QUALITY_JSON__", raw)
        self.assertIn("__STALE_HOURS__", raw)
        quality = build_quality(
            generated_at="2026-09-21T00:00:00Z",
            git={"sha": "abc1234", "branch": "main", "dirty": False},
            suites={
                "api": {
                    "total": 1,
                    "passed": 1,
                    "failed": 0,
                    "skipped": 0,
                    "status": "passed",
                    "duration_s": 0.1,
                }
            },
            checks={"web_in_ci": "missing", "web_tsc": "passed"},
            modules=[
                {
                    "id": "api.events",
                    "layer": "api",
                    "tests": 1,
                    "failed": 0,
                    "status": "passed",
                }
            ],
            failures=[],
        )
        page = render_html(quality)
        self.assertIn("api.events", page)
        self.assertIn("web_in_ci", page)
        json.loads(
            page.split("const data = ", 1)[1].split(";\nfunction badge", 1)[0]
        )


if __name__ == "__main__":
    unittest.main()
