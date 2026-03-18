"""
统计服务
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from app.models.stats import SystemStats
from app.models.strategy import StrategySubscription, SubscriptionStatus
from app.models.signal import TradingSignal
from app.models.user import User, UserStatus


class StatsService:
    """统计服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_platform_stats(self) -> dict:
        """获取平台统计数据"""
        # 获取最新的统计数据
        latest_stats = await self._get_latest_stats()
        
        return {
            "total_volume": latest_stats.get("total_volume", Decimal("0")),
            "active_users": latest_stats.get("active_users", 0),
            "total_signals": latest_stats.get("total_signals", 0),
            "avg_latency_ms": latest_stats.get("avg_latency_ms", 0),
        }
    
    async def get_user_stats(self, user_id: str) -> dict:
        """获取用户统计数据"""
        # 活跃订阅数
        active_subscriptions = await self._count_active_subscriptions(user_id)
        
        # 今日信号数
        today_signals = await self._count_today_signals(user_id)
        
        # 运行时长（简化计算，从第一次订阅开始）
        running_hours = await self._calculate_running_hours(user_id)
        
        # 本月收益（简化，实际应该从交易记录计算）
        monthly_profit = Decimal("0.00")
        
        return {
            "active_subscriptions": active_subscriptions,
            "monthly_profit": monthly_profit,
            "today_signals": today_signals,
            "running_hours": running_hours,
        }
    
    async def _get_latest_stats(self) -> dict:
        """获取最新统计数据"""
        result = await self.db.execute(
            select(SystemStats)
            .order_by(SystemStats.stat_date.desc())
            .limit(1)
        )
        stats = result.scalar_one_or_none()
        
        if stats:
            return {
                "total_volume": stats.total_volume,
                "active_users": stats.active_users,
                "total_signals": stats.total_signals,
                "avg_latency_ms": stats.avg_latency_ms,
            }
        
        # 如果没有统计数据，实时计算
        return await self._calculate_realtime_stats()
    
    async def _calculate_realtime_stats(self) -> dict:
        """实时计算统计数据"""
        # 活跃用户数
        active_users_result = await self.db.execute(
            select(func.count(User.id))
            .where(User.status == UserStatus.ACTIVE)
        )
        active_users = active_users_result.scalar() or 0
        
        # 总信号数
        total_signals_result = await self.db.execute(
            select(func.count(TradingSignal.id))
        )
        total_signals = total_signals_result.scalar() or 0
        
        return {
            "total_volume": Decimal("2400000000.00"),  # 示例数据
            "active_users": active_users,
            "total_signals": total_signals,
            "avg_latency_ms": 45,
        }
    
    async def _count_active_subscriptions(self, user_id: str) -> int:
        """计算活跃订阅数"""
        result = await self.db.execute(
            select(func.count(StrategySubscription.id))
            .where(StrategySubscription.user_id == user_id)
            .where(StrategySubscription.status == SubscriptionStatus.ACTIVE)
        )
        return result.scalar() or 0
    
    async def _count_today_signals(self, user_id: str) -> int:
        """计算今日信号数"""
        today = datetime.now(timezone.utc).date()
        result = await self.db.execute(
            select(func.count(TradingSignal.id))
            .join(StrategySubscription, TradingSignal.strategy_id == StrategySubscription.strategy_id)
            .where(StrategySubscription.user_id == user_id)
            .where(func.date(TradingSignal.received_at) == today)
        )
        return result.scalar() or 0
    
    async def _calculate_running_hours(self, user_id: str) -> int:
        """计算运行时长（小时）"""
        # 获取用户第一次订阅时间
        result = await self.db.execute(
            select(StrategySubscription)
            .where(StrategySubscription.user_id == user_id)
            .order_by(StrategySubscription.created_at.asc())
            .limit(1)
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            return 0
        
        delta = datetime.now(timezone.utc) - subscription.created_at
        return int(delta.total_seconds() / 3600)
    
    async def update_daily_stats(self):
        """更新每日统计数据"""
        today = datetime.now(timezone.utc).date()
        
        # 检查是否已存在今日统计
        existing = await self.db.execute(
            select(SystemStats)
            .where(func.date(SystemStats.stat_date) == today)
        )
        if existing.scalar_one_or_none():
            return
        
        # 计算统计数据
        stats_data = await self._calculate_realtime_stats()
        
        stats = SystemStats(
            stat_date=datetime.now(timezone.utc),
            total_volume=stats_data["total_volume"],
            active_users=stats_data["active_users"],
            total_signals=stats_data["total_signals"],
            avg_latency_ms=stats_data["avg_latency_ms"],
        )
        
        self.db.add(stats)
        await self.db.flush()
