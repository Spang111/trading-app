"""
策略服务
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from datetime import datetime
from app.models.strategy import Strategy, SubscriptionPlan, StrategySubscription, StrategyStatus, PlanType, SubscriptionStatus
from app.schemas.strategy import StrategyCreate, StrategyUpdate, SubscriptionPlanCreate


class StrategyService:
    """策略服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, strategy_id: int) -> Optional[Strategy]:
        """通过 ID 获取策略"""
        return await self.db.get(Strategy, strategy_id)
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Strategy]:
        """获取所有策略"""
        result = await self.db.execute(
            select(Strategy)
            .where(Strategy.status == StrategyStatus.ACTIVE)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def create(self, strategy_in: StrategyCreate) -> Strategy:
        """创建策略"""
        strategy = Strategy(
            name=strategy_in.name,
            description=strategy_in.description,
            apy=strategy_in.apy,
            max_drawdown=strategy_in.max_drawdown,
            win_rate=strategy_in.win_rate,
            monthly_price=strategy_in.monthly_price,
            yearly_price=strategy_in.yearly_price,
            tag=strategy_in.tag,
        )
        self.db.add(strategy)
        await self.db.flush()
        await self.db.refresh(strategy)
        
        # 创建默认的订阅套餐
        await self._create_default_plans(strategy)
        
        return strategy
    
    async def update(self, strategy: Strategy, strategy_in: StrategyUpdate) -> Strategy:
        """更新策略"""
        update_data = strategy_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(strategy, field, value)
        
        await self.db.flush()
        await self.db.refresh(strategy)
        return strategy
    
    async def get_plans(self, strategy_id: int) -> List[SubscriptionPlan]:
        """获取策略的订阅套餐"""
        result = await self.db.execute(
            select(SubscriptionPlan)
            .where(SubscriptionPlan.strategy_id == strategy_id)
            .where(SubscriptionPlan.is_active == True)
        )
        return result.scalars().all()
    
    async def create_plan(self, plan_in: SubscriptionPlanCreate) -> SubscriptionPlan:
        """创建订阅套餐"""
        plan = SubscriptionPlan(
            strategy_id=plan_in.strategy_id,
            plan_type=plan_in.plan_type,
            price=plan_in.price,
            duration_days=plan_in.duration_days,
            profit_share_percent=plan_in.profit_share_percent,
            description=plan_in.description,
        )
        self.db.add(plan)
        await self.db.flush()
        await self.db.refresh(plan)
        return plan
    
    async def _create_default_plans(self, strategy: Strategy):
        """创建默认订阅套餐"""
        # 月套餐
        monthly_plan = SubscriptionPlan(
            strategy_id=strategy.id,
            plan_type=PlanType.MONTHLY,
            price=strategy.monthly_price,
            duration_days=30,
            profit_share_percent=0,
            description=f"{strategy.name} - 月度订阅",
        )
        
        # 年套餐
        yearly_plan = SubscriptionPlan(
            strategy_id=strategy.id,
            plan_type=PlanType.YEARLY,
            price=strategy.yearly_price,
            duration_days=365,
            profit_share_percent=5.00,  # 年套餐赠送 5% 分润
            description=f"{strategy.name} - 年度订阅",
        )
        
        self.db.add_all([monthly_plan, yearly_plan])
        await self.db.flush()
    
    async def get_plan_by_id(self, plan_id: str) -> Optional[SubscriptionPlan]:
        """通过 ID 获取套餐"""
        return await self.db.get(SubscriptionPlan, plan_id)
