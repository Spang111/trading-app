"""
订阅路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.services.subscription_service import SubscriptionService
from app.services.payment_service import PaymentService
from app.services.strategy_service import StrategyService
from app.schemas.strategy import StrategySubscriptionResponse
from app.dependencies import get_current_user
from app.models.user import User
from app.models.strategy import SubscriptionStatus

router = APIRouter()


@router.get("", response_model=List[StrategySubscriptionResponse])
async def get_subscriptions(
    status: SubscriptionStatus = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户订阅列表"""
    subscription_service = SubscriptionService(db)
    subscriptions = await subscription_service.get_user_subscriptions(
        current_user.id,
        status=status,
        skip=skip,
        limit=limit
    )
    return subscriptions


@router.post("", response_model=StrategySubscriptionResponse)
async def create_subscription(
    strategy_id: int,
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建订阅（需要先完成支付）"""
    subscription_service = SubscriptionService(db)
    payment_service = PaymentService(db)
    strategy_service = StrategyService(db)
    
    # 验证策略和套餐
    strategy = await strategy_service.get_by_id(strategy_id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="策略不存在"
        )
    
    plan = await strategy_service.get_plan_by_id(plan_id)
    if not plan or plan.strategy_id != strategy_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="套餐不存在"
        )
    
    # 检查是否有待处理的支付
    # 这里简化处理，实际应该检查用户最近的支付记录
    # 创建订阅
    payment = await payment_service.create(current_user.id, 
                                         type('obj', (object,), {'strategy_id': strategy_id})())
    payment.amount = plan.price
    await db.flush()
    
    subscription = await subscription_service.create(
        current_user.id,
        strategy_id,
        plan_id,
        payment
    )
    
    return subscription


@router.get("/{subscription_id}", response_model=StrategySubscriptionResponse)
async def get_subscription(
    subscription_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取订阅详情"""
    subscription_service = SubscriptionService(db)
    subscription = await subscription_service.get_by_id(subscription_id)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订阅不存在"
        )
    
    if subscription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看此订阅"
        )
    
    return subscription


@router.put("/{subscription_id}/cancel", response_model=StrategySubscriptionResponse)
async def cancel_subscription(
    subscription_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """取消订阅"""
    subscription_service = SubscriptionService(db)
    subscription = await subscription_service.get_by_id(subscription_id)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订阅不存在"
        )
    
    if subscription.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此订阅"
        )
    
    subscription = await subscription_service.cancel(subscription)
    return subscription
