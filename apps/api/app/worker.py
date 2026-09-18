"""Worker entry: `python -m app.worker`. Not an HTTP process."""

from app.jobs.loop import run_worker


def main() -> None:
    run_worker()


if __name__ == "__main__":
    main()
