from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

# Job row statuses. String constants, not a DB enum (KTD11).
JOB_PENDING = "pending"
JOB_RUNNING = "running"
JOB_DONE = "done"
JOB_FAILED = "failed"
JOB_CANCELLED = "cancelled"
JOB_STATUSES = (
    JOB_PENDING,
    JOB_RUNNING,
    JOB_DONE,
    JOB_FAILED,
    JOB_CANCELLED,
)


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[str] = mapped_column(String(255), unique=True)
    segment: Mapped[str] = mapped_column(String(32))
    kind: Mapped[str] = mapped_column(String(32), server_default="crash_drop")
    speed: Mapped[float] = mapped_column(Float)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Case(Base):
    __tablename__ = "cases"
    __table_args__ = (
        # At most one open case per segment; decided rows may repeat (R3).
        Index(
            "uq_cases_one_open_per_segment",
            "segment",
            unique=True,
            postgresql_where=text("status = 'open'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    segment: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), server_default="open")
    drone_status: Mapped[str] = mapped_column(String(32), server_default="idle")
    rationale: Mapped[str | None] = mapped_column(Text)
    trigger_kind: Mapped[str | None] = mapped_column(String(32))
    dispatcher_opinion: Mapped[str | None] = mapped_column(Text)
    critic_opinion: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    audit_entries: Mapped[list["AuditEntry"]] = relationship(back_populates="case")
    jobs: Mapped[list["Job"]] = relationship(back_populates="case")


class AuditEntry(Base):
    __tablename__ = "audit_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"))
    actor: Mapped[str] = mapped_column(String(128))
    action: Mapped[str] = mapped_column(String(64))
    why: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    case: Mapped["Case"] = relationship(back_populates="audit_entries")


class Job(Base):
    """One queue row per case. Claim fields exist so U3 does not alter this table."""

    __tablename__ = "jobs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'running', 'done', 'failed', 'cancelled')",
            name="ck_jobs_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), unique=True)
    status: Mapped[str] = mapped_column(String(32), server_default=JOB_PENDING)
    lease_version: Mapped[int] = mapped_column(Integer, server_default="0")
    attempts: Mapped[int] = mapped_column(Integer, server_default="0")
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    case: Mapped["Case"] = relationship(back_populates="jobs")
