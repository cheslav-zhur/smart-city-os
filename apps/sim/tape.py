"""Canned tapes for segment A: collapse, speeding, jam. HTTP sim only."""

# Match API opening rules in apps/api/app/cases/service.py (KTD8). Sim stays stdlib.
KIND_CRASH_DROP = "crash_drop"
KIND_SPEEDING = "speeding"
KIND_JAM = "jam"
EVENT_KINDS = (KIND_CRASH_DROP, KIND_SPEEDING, KIND_JAM)

MOVING_MIN = 0.0
COLLAPSE_MAX = 0.5
SPEEDING_MIN = 80.0
JAM_MAX = 5.0
JAM_SLOW_WINDOW = 3
JAM_PRIOR_WINDOW = 3

STEP_SECONDS = 2
MOVING_POINTS = 20
MOVING_SPEED = 45.0
SPEEDING_SPEED = 80.0
JAM_FAST_SPEED = 40.0
JAM_SLOW_SPEED = 3.0

# offset_seconds, speed, kind — kind is always set; the API omit-default is not for demo.
Sample = tuple[int, float, str]


def build_collapse_tape() -> list[Sample]:
    samples: list[Sample] = [
        (i * STEP_SECONDS, MOVING_SPEED, KIND_CRASH_DROP) for i in range(MOVING_POINTS)
    ]
    samples.append((MOVING_POINTS * STEP_SECONDS, 0.0, KIND_CRASH_DROP))
    return samples


def build_speeding_tape() -> list[Sample]:
    return [(0, SPEEDING_SPEED, KIND_SPEEDING)]


def build_jam_tape() -> list[Sample]:
    fast = [
        (i * STEP_SECONDS, JAM_FAST_SPEED, KIND_JAM) for i in range(JAM_PRIOR_WINDOW)
    ]
    slow_start = JAM_PRIOR_WINDOW * STEP_SECONDS
    slow = [
        (slow_start + i * STEP_SECONDS, JAM_SLOW_SPEED, KIND_JAM)
        for i in range(JAM_SLOW_WINDOW)
    ]
    return fast + slow


def concat_tapes(*tapes: list[Sample]) -> list[Sample]:
    out: list[Sample] = []
    next_start = 0
    for tape in tapes:
        if not tape:
            continue
        delta = next_start - tape[0][0]
        shifted = [(offset + delta, speed, kind) for offset, speed, kind in tape]
        out.extend(shifted)
        next_start = out[-1][0] + STEP_SECONDS
    return out


COLLAPSE_TAPE = build_collapse_tape()
SPEEDING_TAPE = build_speeding_tape()
JAM_TAPE = build_jam_tape()
MIXED_TAPE = concat_tapes(COLLAPSE_TAPE, SPEEDING_TAPE, JAM_TAPE)


def would_collapse(samples: list[Sample]) -> bool:
    """True if the last two samples are a moving speed then ~0."""
    if len(samples) < 2:
        return False
    previous = samples[-2][1]
    current = samples[-1][1]
    return previous > MOVING_MIN and current <= COLLAPSE_MAX


def would_open_speeding(samples: list[Sample]) -> bool:
    """True if the newest sample is at or over the speeding threshold."""
    if not samples:
        return False
    return samples[-1][1] >= SPEEDING_MIN


def would_open_jam(samples: list[Sample]) -> bool:
    """True if the last three speeds are slow and at least one of the prior three was not."""
    need = JAM_SLOW_WINDOW + JAM_PRIOR_WINDOW
    if len(samples) < need:
        return False
    newest_first = list(reversed(samples))
    slow = newest_first[:JAM_SLOW_WINDOW]
    prior = newest_first[JAM_SLOW_WINDOW:need]
    if any(sample[1] > JAM_MAX for sample in slow):
        return False
    return any(sample[1] > JAM_MAX for sample in prior)
