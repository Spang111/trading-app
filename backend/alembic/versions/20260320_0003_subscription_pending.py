"""Add pending status to strategy subscriptions.

Revision ID: 20260320_0003
Revises: 20260319_0002
Create Date: 2026-03-20
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = "20260320_0003"
down_revision: Union[str, None] = "20260319_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE subscriptionstatus ADD VALUE IF NOT EXISTS 'PENDING'")


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed safely in-place.
    pass
