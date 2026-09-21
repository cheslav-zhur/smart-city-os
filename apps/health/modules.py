"""Hard map: one test file → one dashboard module."""

MODULE_FILES: dict[str, tuple[str, tuple[str, ...]]] = {
    "api.health": ("api", ("test_health.py",)),
    "api.events": ("api", ("test_ingest.py", "test_event_kinds.py")),
    "api.cases": ("api", ("test_hitl.py", "test_console_reads.py")),
    "api.jobs": ("api", ("test_jobs.py",)),
    "api.llm": (
        "api",
        (
            "test_agents.py",
            "test_playbook.py",
            "test_llm_stub.py",
            "test_openai_tool_call_extras.py",
        ),
    ),
    "api.schema": ("api", ("test_schema_v1.py",)),
    "web.cases": ("web", ("CaseCard.test.tsx",)),
    "web.shared": ("web", ("time.test.ts",)),
    "sim.tape": ("sim", ("test_tape.py",)),
    "sim.stream": ("sim", ("test_stream.py",)),
}

FILE_TO_MODULE = {
    filename: module_id
    for module_id, (_layer, files) in MODULE_FILES.items()
    for filename in files
}

MODULE_LAYER = {module_id: layer for module_id, (layer, _files) in MODULE_FILES.items()}
