"""Add cases.rationale for optional card why.

Revision ID: 0002_case_rationale
Revises: 0001_initial
Create Date: 2026-09-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_case_rationale"
down_revision: Union[str, Sequence[str], None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("cases", sa.Column("rationale", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("cases", "rationale")
