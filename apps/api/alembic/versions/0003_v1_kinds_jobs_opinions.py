"""Event kind, case opinions, and the Postgres job table.

Revision ID: 0003_v1_kinds_jobs_opinions
Revises: 0002_case_rationale
Create Date: 2026-09-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_v1_kinds_jobs_opinions"
down_revision: Union[str, Sequence[str], None] = "0002_case_rationale"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column(
            "kind",
            sa.String(32),
            nullable=False,
            server_default="crash_drop",
        ),
    )
    op.add_column("cases", sa.Column("trigger_kind", sa.String(32), nullable=True))
    op.add_column("cases", sa.Column("dispatcher_opinion", sa.Text(), nullable=True))
    op.add_column("cases", sa.Column("critic_opinion", sa.Text(), nullable=True))
    op.create_index(
        "uq_cases_one_open_per_segment",
        "cases",
        ["segment"],
        unique=True,
        postgresql_where=sa.text("status = 'open'"),
    )
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.String(32),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("lease_version", sa.Integer(), server_default="0", nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], name="fk_jobs_case_id"),
        sa.UniqueConstraint("case_id", name="uq_jobs_case_id"),
        sa.CheckConstraint(
            "status IN ('pending', 'running', 'done', 'failed', 'cancelled')",
            name="ck_jobs_status",
        ),
    )


def downgrade() -> None:
    op.drop_table("jobs")
    op.drop_index("uq_cases_one_open_per_segment", table_name="cases")
    op.drop_column("cases", "critic_opinion")
    op.drop_column("cases", "dispatcher_opinion")
    op.drop_column("cases", "trigger_kind")
    op.drop_column("events", "kind")
