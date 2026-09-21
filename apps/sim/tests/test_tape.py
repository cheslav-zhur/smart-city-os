from tape import (
    COLLAPSE_TAPE,
    EVENT_KINDS,
    JAM_TAPE,
    KIND_CRASH_DROP,
    KIND_JAM,
    KIND_SPEEDING,
    MIXED_TAPE,
    SPEEDING_TAPE,
    would_collapse,
    would_open_jam,
    would_open_speeding,
)


def test_canned_collapse_tape_would_open() -> None:
    assert len(COLLAPSE_TAPE) == 21
    assert COLLAPSE_TAPE[0] == (0, 45.0, KIND_CRASH_DROP)
    assert COLLAPSE_TAPE[-2] == (38, 45.0, KIND_CRASH_DROP)
    assert COLLAPSE_TAPE[-1] == (40, 0.0, KIND_CRASH_DROP)
    assert would_collapse(COLLAPSE_TAPE) is True
    assert would_open_speeding(COLLAPSE_TAPE) is False
    assert would_open_jam(COLLAPSE_TAPE) is False


def test_moving_only_is_not_a_collapse() -> None:
    moving = COLLAPSE_TAPE[:-1]
    assert would_collapse(moving) is False


def test_canned_speeding_tape_would_open() -> None:
    assert SPEEDING_TAPE == [(0, 80.0, KIND_SPEEDING)]
    assert would_open_speeding(SPEEDING_TAPE) is True
    assert would_collapse(SPEEDING_TAPE) is False
    assert would_open_jam(SPEEDING_TAPE) is False


def test_canned_jam_tape_would_open() -> None:
    assert len(JAM_TAPE) == 6
    assert JAM_TAPE[0] == (0, 40.0, KIND_JAM)
    assert JAM_TAPE[-1][1] == 3.0
    assert all(kind == KIND_JAM for _t, _speed, kind in JAM_TAPE)
    assert would_open_jam(JAM_TAPE) is True
    assert would_collapse(JAM_TAPE) is False
    assert would_open_speeding(JAM_TAPE) is False


def test_mixed_tape_posts_all_three_kinds() -> None:
    kinds = {kind for _t, _speed, kind in MIXED_TAPE}
    assert kinds == set(EVENT_KINDS)
    assert all(kind in EVENT_KINDS for _t, _speed, kind in MIXED_TAPE)
    assert MIXED_TAPE[0][2] == KIND_CRASH_DROP
    assert any(kind == KIND_SPEEDING for _t, _speed, kind in MIXED_TAPE)
    assert MIXED_TAPE[-1][2] == KIND_JAM
