"""
交易所 API 模型
"""
from sqlalchemy import Column, String, Boolean, Enum, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum


class Exchange(str, enum.Enum):
    """交易所"""
    OKX = "okx"
    BINANCE = "binance"


from app.database import Base


class ExchangeAPI(Base):
    """交易所 API 表"""
    __tablename__ = "exchange_apis"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    exchange = Column(Enum(Exchange), nullable=False)
    api_key = Column(String(255), nullable=False)  # AES 加密存储
    api_secret = Column(String(255), nullable=False)  # AES 加密存储
    passphrase = Column(String(255), nullable=True)  # AES 加密（OKX 需要）
    is_active = Column(Boolean, default=True, nullable=False)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关系
    user = relationship("User", backref="exchange_apis")
