from app.models import Case

DRONE_IDLE = "idle"
DRONE_IN_FLIGHT = "in_flight"
DRONE_ON_SITE = "on_site"


def dispatch_after_approve(case: Case) -> None:
    """Stub: idle → in_flight → on_site in one request. Not a model tool."""
    case.drone_status = DRONE_IN_FLIGHT
    case.drone_status = DRONE_ON_SITE
