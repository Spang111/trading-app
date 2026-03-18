"""
Trading signal models.
"""
import enum
import uuid

from sqlalchemy import Column, DateTime, DECIMAL, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class SignalAction(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, enum.Enum):
    MARKET = "market"
    LIMIT = "limit"


class SignalStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ExecutionStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class SignalSource(str, enum.Enum):
    TRADINGVIEW = "tradingview"
    ADMIN_MANUAL = "admin_manual"


class TradingSignal(Base):
    __tablename__ = "trading_signals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy_id = Column(Integer, ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False)
    source = Column(Enum(SignalSource), default=SignalSource.TRADINGVIEW, nullable=False)
    action = Column(Enum(SignalAction), nullable=False)
    ticker = Column(String(20), nullable=False)
    order_type = Column(Enum(OrderType), nullable=False)
    quantity = Column(DECIMAL(20, 8), nullable=False)
    price = Column(DECIMAL(20, 8), nullable=True)
    leverage = Column(Integer, nullable=True)
    exchange = Column(String(20), nullable=False)
    raw_payload = Column(JSON, nullable=True)
    received_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(SignalStatus), default=SignalStatus.PENDING, nullable=False)

    strategy = relationship("Strategy", back_populates="signals")
    executions = relationship(
        "SignalExecution",
        back_populates="signal",
        cascade="all, delete-orphan",
    )


class SignalExecution(Base):
    __tablename__ = "signal_executions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    signal_id = Column(String(36), ForeignKey("trading_signals.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subscription_id = Column(
        String(36),
        ForeignKey("strategy_subscriptions.id", ondelete="SET NULL"),
        nullable=True,
    )
    exchange_api_id = Column(
        String(36),
        ForeignKey("exchange_apis.id", ondelete="SET NULL"),
        nullable=True,
    )
    order_id = Column(String(100), nullable=True)
    executed_price = Column(DECIMAL(20, 8), nullable=True)
    executed_quantity = Column(DECIMAL(20, 8), nullable=True)
    execution_status = Column(Enum(ExecutionStatus), nullable=False)
    error_message = Column(Text, nullable=True)
    executed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    signal = relationship("TradingSignal", back_populates="executions")
    user = relationship("User")
