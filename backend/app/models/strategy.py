"""
策略相关模型
"""
from sqlalchemy import Column, String, Boolean, Enum, DateTime, ForeignKey, Integer, DECIMAL, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid


class StrategyStatus(str, enum.Enum):
    """策略状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"


class PlanType(str, enum.Enum):
    """套餐类型"""
    MONTHLY = "monthly"
    YEARLY = "yearly"


class SubscriptionStatus(str, enum.Enum):
    """订阅状态"""
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


from app.database import Base


class Strategy(Base):
    """策略表"""
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    apy = Column(DECIMAL(10, 2), nullable=False)  # 年化收益率
    max_drawdown = Column(DECIMAL(10, 2), nullable=False)  # 最大回撤
    win_rate = Column(DECIMAL(5, 2), nullable=False)  # 胜率
    monthly_price = Column(DECIMAL(10, 2), nullable=False)  # 月订阅价格
    yearly_price = Column(DECIMAL(10, 2), nullable=False)  # 年订阅价格
    tag = Column(String(20), nullable=True)  # 标签
    status = Column(Enum(StrategyStatus), default=StrategyStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 关系
    plans = relationship("SubscriptionPlan", back_populates="strategy", cascade="all, delete-orphan")
    subscriptions = relationship("StrategySubscription", back_populates="strategy")
    signals = relationship("TradingSignal", back_populates="strategy")


class SubscriptionPlan(Base):
    """订阅套餐表"""
    __tablename__ = "subscription_plans"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy_id = Column(Integer, ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False)
    plan_type = Column(Enum(PlanType), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    duration_days = Column(Integer, nullable=False)  # 订阅时长（天）
    profit_share_percent = Column(DECIMAL(5, 2), default=0.00)  # 分润比例
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # 关系
    strategy = relationship("Strategy", back_populates="plans")
    subscriptions = relationship("StrategySubscription", back_populates="plan")


class StrategySubscription(Base):
    """策略订阅表"""
    __tablename__ = "strategy_subscriptions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(String(36), ForeignKey("subscription_plans.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False)
    profit_share_percent = Column(DECIMAL(5, 2), default=0.00)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关系
    user = relationship("User", backref="subscriptions")
    strategy = relationship("Strategy", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
