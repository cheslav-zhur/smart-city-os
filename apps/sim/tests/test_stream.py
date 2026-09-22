from itertools import islice

from stream import (
    CALM_POINTS,
    event_id,
    iter_live_samples,
    live_prefix,
)
from tape import (
    KIND_CRASH_DROP,
    KIND_JAM,
    KIND_SPEEDING,
    MIXED_TAPE,
    MOVING_SPEED,
    Sample,
    concat_tapes,
    would_collapse,
    would_open_jam,
    would_open_speeding,
)


def _opening_indexes(samples: list[Sample]) -> list[int]:
    found: list[int] = []
    for index in range(len(samples)):
        window = samples[: index + 1]
        kind = samples[index][2]
        if kind == KIND_CRASH_DROP and would_collapse(window):
            found.append(index)
        elif kind == KIND_SPEEDING and would_open_speeding(window):
            found.append(index)
        elif kind == KIND_JAM and would_open_jam(window):
            found.append(index)
    return found


def _until_openings(count: int) -> list[Sample]:
    samples: list[Sample] = []
    for sample in iter_live_samples():
        samples.append(sample)
        if len(_opening_indexes(samples)) >= count:
            return samples
    raise RuntimeError("live stream ended")


def _has_calm_stretch(samples: list[Sample]) -> bool:
    run = 0
    for _offset, speed, _kind in samples:
        if speed == MOVING_SPEED:
            run += 1
            if run >= CALM_POINTS:
                return True
        else:
            run = 0
    return False


def test_live_prefix_is_not_mixed_tape_replay() -> None:
    replay = concat_tapes(list(MIXED_TAPE), list(MIXED_TAPE))
    prefix = live_prefix(len(replay))
    assert prefix != replay
    assert prefix[: len(MIXED_TAPE)] != list(MIXED_TAPE)


def test_live_event_ids_are_unique() -> None:
    n = 200
    ids = [event_id("run1", index) for index in range(n)]
    assert len(set(ids)) == n
    assert event_id("run1", 0) != event_id("run2", 0)


def test_live_prefix_includes_all_three_kinds() -> None:
    samples = _until_openings(3)
    kinds = {kind for _offset, _speed, kind in samples}
    assert kinds >= {KIND_CRASH_DROP, KIND_SPEEDING, KIND_JAM}
    openings = _opening_indexes(samples)
    opening_kinds = [samples[index][2] for index in openings]
    assert opening_kinds == [KIND_CRASH_DROP, KIND_SPEEDING, KIND_JAM]


def test_calm_stretch_sits_between_opening_sequences() -> None:
    samples = _until_openings(3)
    openings = _opening_indexes(samples)
    assert len(openings) >= 3
    for start, end in zip(openings, openings[1:]):
        between = samples[start + 1 : end]
        assert _has_calm_stretch(between)


def test_live_stream_continues_past_first_opening() -> None:
    gen = iter_live_samples()
    taken = list(islice(gen, 80))
    assert len(taken) == 80
    assert _opening_indexes(taken)
    first_opening = _opening_indexes(taken)[0]
    assert first_opening < len(taken) - 1
    assert next(gen) is not None


def test_second_crash_would_open_after_calm() -> None:
    samples = _until_openings(4)
    openings = _opening_indexes(samples)
    crash_openings = [
        index for index in openings if samples[index][2] == KIND_CRASH_DROP
    ]
    assert len(crash_openings) >= 2
    second = crash_openings[1]
    assert would_collapse(samples[: second + 1]) is True


def test_default_cli_plays_the_canned_tape() -> None:
    import run

    assert run.parse_args([]).live is False
    assert run.parse_args(["--live"]).live is True
