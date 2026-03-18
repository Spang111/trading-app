"""
分润相关模型
"""
from sqlalchemy import Column, String, Boolean, Enum, DateTime, ForeignKey, DECIMAL, Date, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum


class ProfitSharingStatus(str, enum.Enum):
    """分润状态"""
    PENDING = "pending"
    PAID = "paid"


from app.database import Base


class ProfitSharingRule(Base):
    """分润规则表"""
    __tablename__ = "profit_sharing_rules"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    strategy_id = Column(Integer, ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False)
    plan_type = Column(String(20), nullable=False)  # monthly/yearly
    share_percent = Column(DECIMAL(5, 2), nullable=False)
    min_profit_threshold = Column(DECIMAL(20, 8), default=0.00)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 关系
    strategy = relationship("Strategy")


class ProfitSharingRecord(Base):
    """分润记录表"""
    __tablename__ = "profit_sharing_records"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False)
    subscription_id = Column(String(36), ForeignKey("strategy_subscriptions.id", ondelete="SET NULL"), nullable=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    total_profit = Column(DECIMAL(20, 8), nullable=False)
    platform_share = Column(DECIMAL(20, 8), nullable=False)
    user_share = Column(DECIMAL(20, 8), nullable=False)
    status = Column(Enum(ProfitSharingStatus), default=ProfitSharingStatus.PENDING, nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 关系
    user = relationship("User")
    strategy = relationship("Strategy")
