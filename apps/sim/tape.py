"""Canned speed tape for segment A: ~40s moving, then a collapse to 0."""

# Must match the API collapse rule (speed > 0 then speed <= 0.5).
COLLAPSE_MAX = 0.5
STEP_SECONDS = 2
MOVING_POINTS = 20
MOVING_SPEED = 45.0


def build_tape() -> list[tuple[int, float]]:
    samples = [(i * STEP_SECONDS, MOVING_SPEED) for i in range(MOVING_POINTS)]
    samples.append((MOVING_POINTS * STEP_SECONDS, 0.0))
    return samples


TAPE = build_tape()


def would_collapse(samples: list[tuple[int, float]]) -> bool:
    """True if the last two samples are a moving speed then ~0."""
    if len(samples) < 2:
        return False
    _t_prev, previous = samples[-2]
    _t_curr, current = samples[-1]
    return previous > 0.0 and current <= COLLAPSE_MAX
