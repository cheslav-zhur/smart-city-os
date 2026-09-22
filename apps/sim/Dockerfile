# syntax=docker/dockerfile:1
# Hosted live sim. Local stays `python apps/sim/run.py --live` (`docs/dev.md`).

FROM python:3.12-slim-bookworm
WORKDIR /app
COPY apps/sim/run.py apps/sim/stream.py apps/sim/tape.py ./
ENV PORT=8080
ENV CITY_API_ID_TOKEN=1
EXPOSE 8080
CMD ["python", "run.py", "--live"]
