"""
系统统计模型
"""
from sqlalchemy import Column, String, DateTime, Integer, DECIMAL
from sqlalchemy.sql import func
import uuid


from app.database import Base


class SystemStats(Base):
    """系统统计表"""
    __tablename__ = "system_stats"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    stat_date = Column(DateTime(timezone=True), nullable=False, index=True)
    total_volume = Column(DECIMAL(20, 8), default=0.00)  # 累计交易额
    active_users = Column(Integer, default=0)  # 活跃用户数
    total_signals = Column(Integer, default=0)  # 总信号数
    avg_latency_ms = Column(Integer, default=0)  # 平均延迟（毫秒）
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
