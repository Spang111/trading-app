"""
策略相关 Pydantic 模式
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum


class StrategyStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class PlanType(str, Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class StrategyCreate(BaseModel):
    """策略创建"""
    name: str = Field(..., min_length=1, max_length=100, description="策略名称")
    description: Optional[str] = Field(None, description="策略描述")
    apy: Decimal = Field(..., ge=0, description="年化收益率")
    max_drawdown: Decimal = Field(..., ge=0, description="最大回撤")
    win_rate: Decimal = Field(..., ge=0, le=100, description="胜率")
    monthly_price: Decimal = Field(..., ge=0, description="月订阅价格")
    yearly_price: Decimal = Field(..., ge=0, description="年订阅价格")
    tag: Optional[str] = Field(None, max_length=20, description="标签")


class StrategyUpdate(BaseModel):
    """策略更新"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="策略名称")
    description: Optional[str] = Field(None, description="策略描述")
    apy: Optional[Decimal] = Field(None, ge=0, description="年化收益率")
    max_drawdown: Optional[Decimal] = Field(None, ge=0, description="最大回撤")
    win_rate: Optional[Decimal] = Field(None, ge=0, le=100, description="胜率")
    monthly_price: Optional[Decimal] = Field(None, ge=0, description="月订阅价格")
    yearly_price: Optional[Decimal] = Field(None, ge=0, description="年订阅价格")
    tag: Optional[str] = Field(None, max_length=20, description="标签")
    status: Optional[StrategyStatus] = Field(None, description="状态")


class StrategyResponse(BaseModel):
    """策略响应"""
    id: int
    name: str
    description: Optional[str] = None
    apy: Decimal
    max_drawdown: Decimal
    win_rate: Decimal
    monthly_price: Decimal
    yearly_price: Decimal
    tag: Optional[str] = None
    status: StrategyStatus
    created_at: datetime
    
    class Config:
        from_attributes = True


class SubscriptionPlanCreate(BaseModel):
    """订阅套餐创建"""
    strategy_id: int = Field(..., description="策略 ID")
    plan_type: PlanType = Field(..., description="套餐类型")
    price: Decimal = Field(..., ge=0, description="价格")
    duration_days: int = Field(..., gt=0, description="订阅时长（天）")
    profit_share_percent: Decimal = Field(default=0, ge=0, le=100, description="分润比例")
    description: Optional[str] = Field(None, max_length=255, description="套餐描述")


class SubscriptionPlanResponse(BaseModel):
    """订阅套餐响应"""
    id: str
    strategy_id: int
    plan_type: PlanType
    price: Decimal
    duration_days: int
    profit_share_percent: Decimal
    description: Optional[str] = None
    is_active: bool
    
    class Config:
        from_attributes = True


class StrategySubscriptionCreate(BaseModel):
    """策略订阅创建"""
    strategy_id: int = Field(..., description="策略 ID")
    plan_id: str = Field(..., description="套餐 ID")


class StrategySubscriptionResponse(BaseModel):
    """策略订阅响应"""
    id: str
    user_id: int
    strategy_id: int
    plan_id: str
    start_date: datetime
    end_date: datetime
    status: SubscriptionStatus
    profit_share_percent: Decimal
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
