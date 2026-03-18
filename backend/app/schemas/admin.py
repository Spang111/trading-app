"""
Admin trade schemas.
"""
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SignalAction(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"


class ManualTradePayload(BaseModel):
    action: SignalAction = Field(..., description="buy/sell")
    ticker: str = Field(..., description="symbol, e.g. BTCUSDT or BTC/USDT")
    order_type: OrderType = Field(default=OrderType.MARKET)
    quantity: Decimal = Field(..., gt=0)
    price: Optional[Decimal] = None
    exchange: str = Field(default="okx")
    leverage: Optional[int] = Field(default=1, ge=1, le=125)
    strategy_id: int = Field(..., description="strategy id")
