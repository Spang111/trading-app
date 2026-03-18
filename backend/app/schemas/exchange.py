"""
交易所 API 相关 Pydantic 模式
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class Exchange(str, Enum):
    OKX = "okx"
    BINANCE = "binance"


class ExchangeAPICreate(BaseModel):
    """交易所 API 创建"""
    exchange: Exchange = Field(..., description="交易所")
    api_key: str = Field(..., min_length=10, description="API Key")
    api_secret: str = Field(..., min_length=10, description="API Secret")
    passphrase: Optional[str] = Field(None, description="Passphrase（OKX 需要）")


class ExchangeAPIVerify(BaseModel):
    """交易所 API 验证"""
    exchange: Exchange = Field(..., description="交易所")
    api_key: str = Field(..., description="API Key")
    api_secret: str = Field(..., description="API Secret")
    passphrase: Optional[str] = Field(None, description="Passphrase（OKX 需要）")


class ExchangeAPIResponse(BaseModel):
    """交易所 API 响应"""
    id: str
    user_id: int
    exchange: Exchange
    api_key: str  # 仅返回前缀，不返回完整密钥
    is_active: bool
    last_verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
