"""
信号相关 Pydantic 模式
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum


class SignalAction(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"


class SignalStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class SignalResponse(BaseModel):
    """信号响应"""
    id: str
    strategy_id: int
    action: SignalAction
    ticker: str
    order_type: OrderType
    quantity: Decimal
    price: Optional[Decimal] = None
    leverage: Optional[int] = None
    exchange: str
    received_at: datetime
    processed_at: Optional[datetime] = None
    status: SignalStatus
    
    class Config:
        from_attributes = True


class SignalExecutionResponse(BaseModel):
    """信号执行响应"""
    id: str
    signal_id: str
    user_id: int
    subscription_id: Optional[str] = None
    exchange_api_id: Optional[str] = None
    order_id: Optional[str] = None
    executed_price: Optional[Decimal] = None
    executed_quantity: Optional[Decimal] = None
    execution_status: ExecutionStatus
    error_message: Optional[str] = None
    executed_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True
