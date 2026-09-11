from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.db import engine
from app.cases.router import router as cases_router
from app.events.router import router as events_router

app = FastAPI(title="Smart City OS API")
app.include_router(events_router)
app.include_router(cases_router)


@app.get("/health")
def health() -> dict[str, str]:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError as exc:
        raise HTTPException(status_code=503, detail="database unavailable") from exc
    return {"status": "ok"}
