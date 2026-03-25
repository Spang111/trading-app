"""
Strategy-related Pydantic schemas.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class StrategyStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class PlanType(str, Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


class SubscriptionStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class StrategyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Strategy name")
    description: Optional[str] = Field(None, description="Strategy description")
    apy: Decimal = Field(..., ge=0, description="Annual percentage yield")
    max_drawdown: Decimal = Field(..., ge=0, description="Maximum drawdown")
    win_rate: Decimal = Field(..., ge=0, le=100, description="Win rate")
    monthly_price: Decimal = Field(..., ge=0, description="Monthly price")
    yearly_price: Decimal = Field(..., ge=0, description="Yearly price")
    tag: Optional[str] = Field(None, max_length=20, description="Marketplace tag")


class StrategyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Strategy name")
    description: Optional[str] = Field(None, description="Strategy description")
    apy: Optional[Decimal] = Field(None, ge=0, description="Annual percentage yield")
    max_drawdown: Optional[Decimal] = Field(None, ge=0, description="Maximum drawdown")
    win_rate: Optional[Decimal] = Field(None, ge=0, le=100, description="Win rate")
    monthly_price: Optional[Decimal] = Field(None, ge=0, description="Monthly price")
    yearly_price: Optional[Decimal] = Field(None, ge=0, description="Yearly price")
    tag: Optional[str] = Field(None, max_length=20, description="Marketplace tag")
    status: Optional[StrategyStatus] = Field(None, description="Strategy status")


class StrategyResponse(BaseModel):
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
    strategy_id: int = Field(..., description="Strategy ID")
    plan_type: PlanType = Field(..., description="Plan type")
    price: Decimal = Field(..., ge=0, description="Plan price")
    duration_days: int = Field(..., gt=0, description="Subscription duration in days")
    profit_share_percent: Decimal = Field(default=0, ge=0, le=100, description="Profit share")
    description: Optional[str] = Field(None, max_length=255, description="Plan description")


class SubscriptionPlanResponse(BaseModel):
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
    strategy_id: int = Field(..., description="Strategy ID")
    plan_id: str = Field(..., description="Plan ID")


class StrategySubscriptionResponse(BaseModel):
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
