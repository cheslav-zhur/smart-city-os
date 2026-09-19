"""Playbook search is pure files — no Postgres (KTD7 / V1-U4)."""

from pathlib import Path

from app.llm.playbook import (
    DEFAULT_PLAYBOOKS_ROOT,
    MAX_CHUNK_CHARS,
    search_playbook,
)


def test_default_playbooks_root_is_packaged() -> None:
    """Wheels and editable installs must expose the playbooks package dir."""
    assert DEFAULT_PLAYBOOKS_ROOT.is_dir()
    assert any(DEFAULT_PLAYBOOKS_ROOT.glob("*.md"))


def test_query_matching_heading_returns_file_chunk() -> None:
    hits = search_playbook("Crash look", root=DEFAULT_PLAYBOOKS_ROOT)

    assert len(hits) == 1
    assert hits[0].startswith("# Crash look")
    assert "Propose a short drone look" in hits[0]
    assert len(hits[0]) <= MAX_CHUNK_CHARS


def test_no_match_returns_empty_list() -> None:
    assert search_playbook("subway timetable", root=DEFAULT_PLAYBOOKS_ROOT) == []


def test_missing_playbooks_dir_returns_empty_list(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "no-such-playbooks"
    assert not missing.exists()
    assert search_playbook("crash", root=missing) == []


def test_filename_match_and_chunk_truncate(tmp_path: Path) -> None:
    (tmp_path / "speeding.md").write_text(
        "# Speeding\n" + ("x" * (MAX_CHUNK_CHARS + 50)),
        encoding="utf-8",
    )
    (tmp_path / "other.md").write_text("# Unrelated\nnope\n", encoding="utf-8")

    hits = search_playbook("speeding", root=tmp_path)

    assert len(hits) == 1
    assert len(hits[0]) == MAX_CHUNK_CHARS
    assert hits[0].startswith("# Speeding")


def test_whitespace_only_query_returns_empty(
    tmp_path: Path,
) -> None:
    (tmp_path / "a.md").write_text("# Has spaces in body\n", encoding="utf-8")

    assert search_playbook(" ", root=tmp_path) == []
    assert search_playbook("\t\n", root=tmp_path) == []


def test_non_utf8_file_is_skipped(tmp_path: Path) -> None:
    (tmp_path / "bad.md").write_bytes(b"\xff\xfe not utf-8")
    (tmp_path / "good.md").write_text(
        "# Good\nlook for crash here\n", encoding="utf-8"
    )

    hits = search_playbook("crash", root=tmp_path)

    assert len(hits) == 1
    assert hits[0].startswith("# Good")


def test_top_three_cap(tmp_path: Path) -> None:
    for name in ("a.md", "b.md", "c.md", "d.md"):
        (tmp_path / name).write_text(f"# {name}\nshared needle\n", encoding="utf-8")

    hits = search_playbook("shared needle", root=tmp_path)

    assert len(hits) == 3
    assert hits[0].startswith("# a.md")
    assert hits[1].startswith("# b.md")
    assert hits[2].startswith("# c.md")
