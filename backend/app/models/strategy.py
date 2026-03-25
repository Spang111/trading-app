"""
Strategy-related SQLAlchemy models.
"""

import enum
import uuid

from sqlalchemy import Boolean, Column, DateTime, DECIMAL, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class StrategyStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class PlanType(str, enum.Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


class SubscriptionStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    apy = Column(DECIMAL(10, 2), nullable=False)
    max_drawdown = Column(DECIMAL(10, 2), nullable=False)
    win_rate = Column(DECIMAL(5, 2), nullable=False)
    monthly_price = Column(DECIMAL(10, 2), nullable=False)
    yearly_price = Column(DECIMAL(10, 2), nullable=False)
    tag = Column(String(20), nullable=True)
    status = Column(Enum(StrategyStatus), default=StrategyStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    plans = relationship("SubscriptionPlan", back_populates="strategy", cascade="all, delete-orphan")
    subscriptions = relationship("StrategySubscription", back_populates="strategy")
    signals = relationship("TradingSignal", back_populates="strategy")


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy_id = Column(Integer, ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False)
    plan_type = Column(Enum(PlanType), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    duration_days = Column(Integer, nullable=False)
    profit_share_percent = Column(DECIMAL(5, 2), default=0.00)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    strategy = relationship("Strategy", back_populates="plans")
    subscriptions = relationship("StrategySubscription", back_populates="plan")


class StrategySubscription(Base):
    __tablename__ = "strategy_subscriptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(String(36), ForeignKey("subscription_plans.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.PENDING, nullable=False)
    profit_share_percent = Column(DECIMAL(5, 2), default=0.00)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", backref="subscriptions")
    strategy = relationship("Strategy", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
