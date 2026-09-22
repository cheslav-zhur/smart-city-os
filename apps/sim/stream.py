"""Procedural live incident stream for segment A. HTTP sim only.

Calm moving samples sit between opening sequences so the shift is readable
and a crash-zero tail can open again. MIXED_TAPE stays the canned fixture.
"""

from __future__ import annotations

from collections.abc import Iterator
from itertools import cycle

from tape import (
    COLLAPSE_TAPE,
    EVENT_KINDS,
    JAM_TAPE,
    KIND_CRASH_DROP,
    KIND_JAM,
    KIND_SPEEDING,
    MOVING_SPEED,
    SPEEDING_TAPE,
    STEP_SECONDS,
    Sample,
    concat_tapes,
)

# Enough moving samples for jam's prior window, then a short breath. Not a hold.
CALM_POINTS = 6

OPENING_TAPES = {
    KIND_CRASH_DROP: COLLAPSE_TAPE,
    KIND_SPEEDING: SPEEDING_TAPE,
    KIND_JAM: JAM_TAPE,
}


def build_calm_tape() -> list[Sample]:
    return [
        (i * STEP_SECONDS, MOVING_SPEED, KIND_CRASH_DROP) for i in range(CALM_POINTS)
    ]


def event_id(run_id: str, index: int) -> str:
    """Unique id for one posted sample in a sim run."""
    return f"sim-{run_id}-{index:06d}"


def iter_live_samples() -> Iterator[Sample]:
    """Endless calm-then-opening cycle: crash_drop, speeding, jam."""
    clock = 0
    for kind in cycle(EVENT_KINDS):
        block = concat_tapes(build_calm_tape(), list(OPENING_TAPES[kind]))
        for offset, speed, sample_kind in block:
            yield (clock + offset, speed, sample_kind)
        clock += block[-1][0] + STEP_SECONDS


def live_prefix(count: int) -> list[Sample]:
    """First `count` live samples. The underlying stream does not end."""
    out: list[Sample] = []
    for sample in iter_live_samples():
        out.append(sample)
        if len(out) >= count:
            return out
    raise RuntimeError("live stream ended")
