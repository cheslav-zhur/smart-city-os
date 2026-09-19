"""Worker entry: `python -m app.worker`. Not an HTTP process."""

import structlog

from app.jobs.loop import run_worker
from app.logging_setup import configure_logging
from app.settings import get_settings


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    log = structlog.get_logger("app.worker")
    log.info(
        "worker_starting",
        log_level=settings.log_level.upper(),
        llm_configured=bool(settings.llm_api_key),
    )
    run_worker()


if __name__ == "__main__":
    main()
