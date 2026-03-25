"""
Strategy service helpers.
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.strategy import (
    PlanType,
    Strategy,
    StrategyStatus,
    SubscriptionPlan,
)
from app.schemas.strategy import StrategyCreate, StrategyUpdate, SubscriptionPlanCreate


class StrategyService:
    """Strategy service class."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, strategy_id: int) -> Optional[Strategy]:
        """Return a strategy by ID."""
        return await self.db.get(Strategy, strategy_id)

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        *,
        include_inactive: bool = False,
    ) -> List[Strategy]:
        """Return strategies for marketplace or admin management."""
        query = select(Strategy)

        if not include_inactive:
            query = query.where(Strategy.status == StrategyStatus.ACTIVE)

        result = await self.db.execute(
            query.order_by(Strategy.created_at.desc()).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def create(self, strategy_in: StrategyCreate) -> Strategy:
        """Create a strategy and its default plans."""
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

        await self._create_default_plans(strategy)

        return strategy

    async def update(self, strategy: Strategy, strategy_in: StrategyUpdate) -> Strategy:
        """Update a strategy in place."""
        update_data = strategy_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(strategy, field, value)

        await self.db.flush()
        await self.db.refresh(strategy)
        return strategy

    async def get_plans(self, strategy_id: int) -> List[SubscriptionPlan]:
        """Return active plans for a strategy."""
        result = await self.db.execute(
            select(SubscriptionPlan)
            .where(SubscriptionPlan.strategy_id == strategy_id)
            .where(SubscriptionPlan.is_active.is_(True))
        )
        return result.scalars().all()

    async def create_plan(self, plan_in: SubscriptionPlanCreate) -> SubscriptionPlan:
        """Create a subscription plan."""
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

    async def _create_default_plans(self, strategy: Strategy) -> None:
        """Create monthly and yearly plans after a strategy is created."""
        monthly_plan = SubscriptionPlan(
            strategy_id=strategy.id,
            plan_type=PlanType.MONTHLY,
            price=strategy.monthly_price,
            duration_days=30,
            profit_share_percent=0,
            description=f"{strategy.name} - monthly subscription",
        )

        yearly_plan = SubscriptionPlan(
            strategy_id=strategy.id,
            plan_type=PlanType.YEARLY,
            price=strategy.yearly_price,
            duration_days=365,
            profit_share_percent=5.00,
            description=f"{strategy.name} - yearly subscription",
        )

        self.db.add_all([monthly_plan, yearly_plan])
        await self.db.flush()

    async def get_plan_by_id(self, plan_id: str) -> Optional[SubscriptionPlan]:
        """Return a plan by ID."""
        return await self.db.get(SubscriptionPlan, plan_id)
