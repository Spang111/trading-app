"""Add email verification fields to users.

Revision ID: 20260319_0002
Revises: 20260316_0001
Create Date: 2026-03-19
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260319_0002"
down_revision: Union[str, None] = "20260316_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "email_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "users",
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "email_verification_sent_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE users
        SET email_verified = TRUE,
            email_verified_at = COALESCE(updated_at, created_at, now())
        WHERE status = 'ACTIVE'
        """
    )


def downgrade() -> None:
    op.drop_column("users", "email_verification_sent_at")
    op.drop_column("users", "email_verified_at")
    op.drop_column("users", "email_verified")
