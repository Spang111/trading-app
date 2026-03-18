"""
Webhook 相关 Pydantic 模式
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum


class SignalAction(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"


class WebhookConfigCreate(BaseModel):
    """Webhook 配置创建"""
    strategy_id: int = Field(..., description="策略 ID")
    allowed_ips: Optional[List[str]] = Field(None, description="IP 白名单列表")


class WebhookConfigResponse(BaseModel):
    """Webhook 配置响应"""
    id: str
    user_id: int
    strategy_id: int
    webhook_url: str
    secret_key: str
    allowed_ips: Optional[List[str]] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WebhookPayload(BaseModel):
    """TradingView Webhook Payload"""
    action: SignalAction = Field(..., description="动作：buy/sell")
    ticker: str = Field(..., description="交易对，如：BTCUSDT")
    order_type: OrderType = Field(default=OrderType.MARKET, description="订单类型")
    quantity: Decimal = Field(..., gt=0, description="数量")
    price: Optional[Decimal] = Field(None, description="价格")
    timestamp: Optional[str] = Field(None, description="时间戳")
    passphrase: str = Field(..., description="密钥验证")
    exchange: str = Field(default="okx", description="交易所")
    leverage: Optional[int] = Field(1, ge=1, le=125, description="杠杆倍数")
    strategy_id: Optional[int] = Field(None, description="策略 ID")
