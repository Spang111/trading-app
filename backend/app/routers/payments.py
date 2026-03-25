"""
Payment routes.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_admin_user, get_current_user
from app.models.payment import PaymentStatus
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentResponse, PaymentVerify
from app.services.payment_service import PaymentService
from app.services.strategy_service import StrategyService
from app.services.subscription_service import SubscriptionService


router = APIRouter()


@router.post("/create", response_model=PaymentResponse)
async def create_payment(
    payment_in: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a pending payment and a pending subscription."""
    payment_service = PaymentService(db)
    strategy_service = StrategyService(db)
    subscription_service = SubscriptionService(db)

    strategy = await strategy_service.get_by_id(payment_in.strategy_id)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found.",
        )

    plans = await strategy_service.get_plans(payment_in.strategy_id)
    plan = next((item for item in plans if item.plan_type.value == payment_in.plan_type), None)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription plan not found.",
        )

    payment = await payment_service.create(current_user.id, payment_in)
    payment.amount = plan.price
    await db.flush()

    await subscription_service.create(
        current_user.id,
        payment_in.strategy_id,
        plan.id,
        payment,
        activate=False,
    )

    await db.refresh(payment)

    return PaymentResponse.from_payment(
        payment,
        **payment_service.get_manual_payment_details(float(plan.price)),
    )


@router.post("/verify")
async def verify_payment(
    payment_verify: PaymentVerify,
    payment_id: str = Query(..., description="Payment ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a TxHash for manual review."""
    payment_service = PaymentService(db)

    payment = await payment_service.get_by_id(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment record not found.",
        )

    if payment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to update this payment.",
        )

    payment = await payment_service.update_status(
        payment,
        PaymentStatus.PENDING,
        tx_hash=payment_verify.tx_hash,
    )

    return {
        "message": "TxHash submitted. Your payment is now waiting for admin review.",
        "payment_id": payment.id,
        "subscription_id": payment.subscription_id,
    }


@router.get("/history", response_model=List[PaymentResponse])
async def get_payment_history(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    payment_service = PaymentService(db)
    payments = await payment_service.get_user_payments(current_user.id, skip=skip, limit=limit)
    return [PaymentResponse.from_payment(payment) for payment in payments]


@router.get("/admin/pending", response_model=List[PaymentResponse])
async def get_pending_payments_for_admin(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    del current_user
    payment_service = PaymentService(db)
    payments = await payment_service.get_pending_payments(skip=skip, limit=limit)
    return [PaymentResponse.from_payment(payment) for payment in payments]


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    payment_service = PaymentService(db)
    payment = await payment_service.get_by_id(payment_id)

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment record not found.",
        )

    if payment.user_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to view this payment.",
        )

    return PaymentResponse.from_payment(payment)


@router.post("/admin/{payment_id}/approve")
async def approve_payment(
    payment_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    payment_service = PaymentService(db)
    subscription_service = SubscriptionService(db)

    payment = await payment_service.get_by_id(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment record not found.",
        )

    payment = await payment_service.verify_payment(
        payment,
        tx_hash=payment.tx_hash or "manual_approved",
        admin_user_id=current_user.id,
    )

    if payment.subscription_id:
        subscription = await subscription_service.get_by_id(payment.subscription_id)
        if subscription:
            await subscription_service.activate(subscription)

    return {"message": "Payment approved and subscription activated."}
