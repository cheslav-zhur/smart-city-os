from tape import TAPE, would_collapse


def test_canned_tape_is_a_collapse() -> None:
    assert len(TAPE) == 21
    assert TAPE[0] == (0, 45.0)
    assert TAPE[-2] == (38, 45.0)
    assert TAPE[-1] == (40, 0.0)
    assert would_collapse(TAPE) is True


def test_moving_only_is_not_a_collapse() -> None:
    moving = TAPE[:-1]
    assert would_collapse(moving) is False
