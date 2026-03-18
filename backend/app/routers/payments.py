"""
支付路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.services.payment_service import PaymentService
from app.services.subscription_service import SubscriptionService
from app.services.strategy_service import StrategyService
from app.schemas.payment import PaymentCreate, PaymentResponse, PaymentVerify
from app.dependencies import get_current_user, get_current_admin_user
from app.models.user import User
from app.models.payment import PaymentStatus

router = APIRouter()


@router.post("/create", response_model=PaymentResponse)
async def create_payment(
    payment_in: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建支付订单"""
    payment_service = PaymentService(db)
    strategy_service = StrategyService(db)
    
    # 验证策略是否存在
    strategy = await strategy_service.get_by_id(payment_in.strategy_id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="策略不存在"
        )
    
    # 获取套餐价格
    plans = await strategy_service.get_plans(payment_in.strategy_id)
    plan = next((p for p in plans if p.plan_type.value == payment_in.plan_type), None)
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="套餐不存在"
        )
    
    # 创建支付记录（人工审核模式）
    payment = await payment_service.create(current_user.id, payment_in)
    payment.amount = plan.price
    
    await db.flush()
    await db.refresh(payment)
    
    return payment


@router.post("/verify")
async def verify_payment(
    payment_verify: PaymentVerify,
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """提交 TxHash 验证（人工审核模式）"""
    payment_service = PaymentService(db)
    
    payment = await payment_service.get_by_id(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="支付记录不存在"
        )
    
    if payment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此支付记录"
        )
    
    # 更新支付记录
    payment = await payment_service.update_status(
        payment, 
        PaymentStatus.PENDING,
        tx_hash=payment_verify.tx_hash
    )
    
    return {"message": "已提交审核，管理员确认后即可激活订阅"}


@router.get("/history", response_model=List[PaymentResponse])
async def get_payment_history(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取支付历史"""
    payment_service = PaymentService(db)
    payments = await payment_service.get_user_payments(
        current_user.id, 
        skip=skip, 
        limit=limit
    )
    return payments


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取支付详情"""
    payment_service = PaymentService(db)
    payment = await payment_service.get_by_id(payment_id)
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="支付记录不存在"
        )
    
    if payment.user_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看此支付记录"
        )
    
    return payment


@router.post("/admin/{payment_id}/approve")
async def approve_payment(
    payment_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """审核通过支付（管理员）"""
    payment_service = PaymentService(db)
    subscription_service = SubscriptionService(db)
    
    payment = await payment_service.get_by_id(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="支付记录不存在"
        )
    
    # 验证支付
    payment = await payment_service.verify_payment(
        payment, 
        tx_hash=payment.tx_hash or "manual_approved",
        admin_user_id=current_user.id
    )
    
    # 如果有订阅 ID，激活订阅
    if payment.subscription_id:
        subscription = await subscription_service.get_by_id(payment.subscription_id)
        if subscription:
            subscription.status = "active"
            await db.flush()
    
    return {"message": "支付已审核通过"}
