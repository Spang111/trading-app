"""
Subscription service.
"""
from datetime import datetime, timedelta
from datetime import timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment, PaymentStatus
from app.models.strategy import StrategySubscription, SubscriptionPlan, SubscriptionStatus


class SubscriptionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, subscription_id: str) -> Optional[StrategySubscription]:
        return await self.db.get(StrategySubscription, subscription_id)

    async def create(
        self,
        user_id: int,
        strategy_id: int,
        plan_id: str,
        payment: Payment,
    ) -> StrategySubscription:
        plan = await self.db.get(SubscriptionPlan, plan_id)
        if not plan:
            raise ValueError("plan_not_found")

        start_date = datetime.now(timezone.utc)
        end_date = start_date + timedelta(days=plan.duration_days)

        subscription = StrategySubscription(
            user_id=user_id,
            strategy_id=strategy_id,
            plan_id=plan_id,
            start_date=start_date,
            end_date=end_date,
            status=SubscriptionStatus.ACTIVE,
            profit_share_percent=plan.profit_share_percent,
        )
        self.db.add(subscription)

        payment.subscription_id = subscription.id
        payment.status = PaymentStatus.SUCCESS
        payment.paid_at = start_date

        await self.db.flush()
        await self.db.refresh(subscription)
        return subscription

    async def get_user_subscriptions(
        self,
        user_id: int,
        status: Optional[SubscriptionStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[StrategySubscription]:
        query = select(StrategySubscription).where(StrategySubscription.user_id == user_id)
        if status:
            query = query.where(StrategySubscription.status == status)
        query = query.order_by(StrategySubscription.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def cancel(self, subscription: StrategySubscription) -> StrategySubscription:
        subscription.status = SubscriptionStatus.CANCELLED
        await self.db.flush()
        await self.db.refresh(subscription)
        return subscription

    async def get_active_subscriptions_by_strategy(
        self,
        strategy_id: int,
    ) -> List[StrategySubscription]:
        result = await self.db.execute(
            select(StrategySubscription)
            .where(StrategySubscription.strategy_id == strategy_id)
            .where(StrategySubscription.status == SubscriptionStatus.ACTIVE)
        )
        return result.scalars().all()

    async def check_subscription_status(self, subscription: StrategySubscription) -> SubscriptionStatus:
        if subscription.status == SubscriptionStatus.ACTIVE:
            if datetime.now(timezone.utc) > subscription.end_date:
                subscription.status = SubscriptionStatus.EXPIRED
                await self.db.flush()
        return subscription.status
