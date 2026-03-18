"""Initial schema.

Revision ID: 20260316_0001
Revises:
Create Date: 2026-03-16

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260316_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    userrole = sa.Enum("USER", "ADMIN", name="userrole")
    userstatus = sa.Enum("ACTIVE", "SUSPENDED", name="userstatus")
    strategystatus = sa.Enum("ACTIVE", "INACTIVE", name="strategystatus")
    plantype = sa.Enum("MONTHLY", "YEARLY", name="plantype")
    subscriptionstatus = sa.Enum(
        "ACTIVE", "EXPIRED", "CANCELLED", name="subscriptionstatus"
    )
    exchange = sa.Enum("OKX", "BINANCE", name="exchange")
    paymentmethod = sa.Enum("NOWPAYMENTS", "MANUAL_WALLET", name="paymentmethod")
    paymentstatus = sa.Enum("PENDING", "SUCCESS", "FAILED", name="paymentstatus")
    signalsource = sa.Enum("TRADINGVIEW", "ADMIN_MANUAL", name="signalsource")
    signalaction = sa.Enum("BUY", "SELL", name="signalaction")
    ordertype = sa.Enum("MARKET", "LIMIT", name="ordertype")
    signalstatus = sa.Enum(
        "PENDING", "PROCESSING", "COMPLETED", "FAILED", name="signalstatus"
    )
    executionstatus = sa.Enum("SUCCESS", "FAILED", "PARTIAL", name="executionstatus")
    profitsharingstatus = sa.Enum("PENDING", "PAID", name="profitsharingstatus")

    for enum_type in (
        userrole,
        userstatus,
        strategystatus,
        plantype,
        subscriptionstatus,
        exchange,
        paymentmethod,
        paymentstatus,
        signalsource,
        signalaction,
        ordertype,
        signalstatus,
        executionstatus,
        profitsharingstatus,
    ):
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("wallet_address", sa.String(length=100), nullable=True),
        sa.Column("role", userrole, nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("status", userstatus, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "strategies",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("apy", sa.Numeric(10, 2), nullable=False),
        sa.Column("max_drawdown", sa.Numeric(10, 2), nullable=False),
        sa.Column("win_rate", sa.Numeric(5, 2), nullable=False),
        sa.Column("monthly_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("yearly_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("tag", sa.String(length=20), nullable=True),
        sa.Column("status", strategystatus, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "subscription_plans",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("strategy_id", sa.Integer(), nullable=False),
        sa.Column("plan_type", plantype, nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("profit_share_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["strategy_id"],
            ["strategies.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "strategy_subscriptions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("strategy_id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.String(length=36), nullable=False),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", subscriptionstatus, nullable=False),
        sa.Column("profit_share_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["plan_id"], ["subscription_plans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "exchange_apis",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("exchange", exchange, nullable=False),
        sa.Column("api_key", sa.String(length=255), nullable=False),
        sa.Column("api_secret", sa.String(length=255), nullable=False),
        sa.Column("passphrase", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "webhook_configs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("strategy_id", sa.Integer(), nullable=False),
        sa.Column("webhook_url", sa.String(length=255), nullable=False),
        sa.Column("secret_key", sa.String(length=255), nullable=False),
        sa.Column("allowed_ips", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "trading_signals",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("strategy_id", sa.Integer(), nullable=False),
        sa.Column("source", signalsource, nullable=False),
        sa.Column("action", signalaction, nullable=False),
        sa.Column("ticker", sa.String(length=20), nullable=False),
        sa.Column("order_type", ordertype, nullable=False),
        sa.Column("quantity", sa.Numeric(20, 8), nullable=False),
        sa.Column("price", sa.Numeric(20, 8), nullable=True),
        sa.Column("leverage", sa.Integer(), nullable=True),
        sa.Column("exchange", sa.String(length=20), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", signalstatus, nullable=False),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "signal_executions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("signal_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("subscription_id", sa.String(length=36), nullable=True),
        sa.Column("exchange_api_id", sa.String(length=36), nullable=True),
        sa.Column("order_id", sa.String(length=100), nullable=True),
        sa.Column("executed_price", sa.Numeric(20, 8), nullable=True),
        sa.Column("executed_quantity", sa.Numeric(20, 8), nullable=True),
        sa.Column("execution_status", executionstatus, nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "executed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["exchange_api_id"], ["exchange_apis.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["signal_id"], ["trading_signals.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["subscription_id"], ["strategy_subscriptions.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "payments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("subscription_id", sa.String(length=36), nullable=True),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("payment_method", paymentmethod, nullable=False),
        sa.Column("tx_hash", sa.String(length=100), nullable=True),
        sa.Column("status", paymentstatus, nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_by", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["strategy_subscriptions.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["verified_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "profit_sharing_rules",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("strategy_id", sa.Integer(), nullable=False),
        sa.Column("plan_type", sa.String(length=20), nullable=False),
        sa.Column("share_percent", sa.Numeric(5, 2), nullable=False),
        sa.Column("min_profit_threshold", sa.Numeric(20, 8), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "profit_sharing_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("strategy_id", sa.Integer(), nullable=False),
        sa.Column("subscription_id", sa.String(length=36), nullable=True),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("total_profit", sa.Numeric(20, 8), nullable=False),
        sa.Column("platform_share", sa.Numeric(20, 8), nullable=False),
        sa.Column("user_share", sa.Numeric(20, 8), nullable=False),
        sa.Column("status", profitsharingstatus, nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["strategy_subscriptions.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "system_stats",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("stat_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_volume", sa.Numeric(20, 8), nullable=True),
        sa.Column("active_users", sa.Integer(), nullable=True),
        sa.Column("total_signals", sa.Integer(), nullable=True),
        sa.Column("avg_latency_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_system_stats_stat_date", "system_stats", ["stat_date"])


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_index("ix_system_stats_stat_date", table_name="system_stats")
    op.drop_table("system_stats")
    op.drop_table("profit_sharing_records")
    op.drop_table("profit_sharing_rules")
    op.drop_table("payments")
    op.drop_table("signal_executions")
    op.drop_table("trading_signals")
    op.drop_table("webhook_configs")
    op.drop_table("exchange_apis")
    op.drop_table("strategy_subscriptions")
    op.drop_table("subscription_plans")
    op.drop_table("strategies")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    profitsharingstatus = sa.Enum("PENDING", "PAID", name="profitsharingstatus")
    executionstatus = sa.Enum("SUCCESS", "FAILED", "PARTIAL", name="executionstatus")
    signalstatus = sa.Enum(
        "PENDING", "PROCESSING", "COMPLETED", "FAILED", name="signalstatus"
    )
    ordertype = sa.Enum("MARKET", "LIMIT", name="ordertype")
    signalaction = sa.Enum("BUY", "SELL", name="signalaction")
    signalsource = sa.Enum("TRADINGVIEW", "ADMIN_MANUAL", name="signalsource")
    paymentstatus = sa.Enum("PENDING", "SUCCESS", "FAILED", name="paymentstatus")
    paymentmethod = sa.Enum("NOWPAYMENTS", "MANUAL_WALLET", name="paymentmethod")
    exchange = sa.Enum("OKX", "BINANCE", name="exchange")
    subscriptionstatus = sa.Enum(
        "ACTIVE", "EXPIRED", "CANCELLED", name="subscriptionstatus"
    )
    plantype = sa.Enum("MONTHLY", "YEARLY", name="plantype")
    strategystatus = sa.Enum("ACTIVE", "INACTIVE", name="strategystatus")
    userstatus = sa.Enum("ACTIVE", "SUSPENDED", name="userstatus")
    userrole = sa.Enum("USER", "ADMIN", name="userrole")

    for enum_type in (
        profitsharingstatus,
        executionstatus,
        signalstatus,
        ordertype,
        signalaction,
        signalsource,
        paymentstatus,
        paymentmethod,
        exchange,
        subscriptionstatus,
        plantype,
        strategystatus,
        userstatus,
        userrole,
    ):
        enum_type.drop(bind, checkfirst=True)

