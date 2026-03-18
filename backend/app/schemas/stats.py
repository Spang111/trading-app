"""
统计相关 Pydantic 模式
"""
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal


class PlatformStatsResponse(BaseModel):
    """平台统计响应"""
    total_volume: Decimal = Field(..., description="累计交易额")
    active_users: int = Field(..., description="活跃用户数")
    total_signals: int = Field(..., description="总信号数")
    avg_latency_ms: int = Field(..., description="平均延迟")


class UserStatsResponse(BaseModel):
    """用户统计响应"""
    active_subscriptions: int = Field(..., description="活跃订阅数")
    monthly_profit: Decimal = Field(..., description="本月收益")
    today_signals: int = Field(..., description="今日信号数")
    running_hours: int = Field(..., description="运行时长（小时）")
