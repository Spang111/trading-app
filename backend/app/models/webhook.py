"""
Webhook 配置模型
"""
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid


from app.database import Base


class WebhookConfig(Base):
    """Webhook 配置表"""
    __tablename__ = "webhook_configs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False)
    webhook_url = Column(String(255), nullable=False)
    secret_key = Column(String(255), nullable=False)
    allowed_ips = Column(Text, nullable=True)  # JSON 数组存储 IP 白名单
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关系
    user = relationship("User", backref="webhook_configs")
    strategy = relationship("Strategy", backref="webhook_configs")
