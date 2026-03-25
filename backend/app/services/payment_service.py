"""
Payment service.
"""

from datetime import datetime, timezone
from typing import List, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.schemas.payment import PaymentCreate


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, payment_id: str) -> Optional[Payment]:
        return await self.db.get(Payment, payment_id)

    async def create(self, user_id: int, payment_in: PaymentCreate) -> Payment:
        payment = Payment(
            user_id=user_id,
            amount=0,
            payment_method=PaymentMethod.MANUAL_WALLET,
            status=PaymentStatus.PENDING,
        )
        self.db.add(payment)
        await self.db.flush()
        await self.db.refresh(payment)
        return payment

    async def update_status(
        self,
        payment: Payment,
        status: PaymentStatus,
        tx_hash: Optional[str] = None,
        verified_by: Optional[int] = None,
    ) -> Payment:
        payment.status = status
        if tx_hash:
            payment.tx_hash = tx_hash
        if verified_by:
            payment.verified_by = verified_by
        if status == PaymentStatus.SUCCESS:
            now = datetime.now(timezone.utc)
            payment.paid_at = now
            payment.verified_at = now

        await self.db.flush()
        await self.db.refresh(payment)
        return payment

    async def get_user_payments(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Payment]:
        result = await self.db.execute(
            select(Payment)
            .where(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_pending_payments(self, skip: int = 0, limit: int = 100) -> List[Payment]:
        result = await self.db.execute(
            select(Payment)
            .where(Payment.status == PaymentStatus.PENDING)
            .order_by(Payment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def verify_payment(self, payment: Payment, tx_hash: str, admin_user_id: int) -> Payment:
        payment.tx_hash = tx_hash
        payment.verified_by = admin_user_id
        now = datetime.now(timezone.utc)
        payment.verified_at = now
        payment.status = PaymentStatus.SUCCESS
        payment.paid_at = now

        await self.db.flush()
        await self.db.refresh(payment)
        return payment

    async def create_nowpayments_invoice(
        self,
        user_id: int,
        strategy_id: int,
        plan_type: str,
        amount: float,
    ) -> dict:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{settings.NOWPAYMENTS_API_URL}/payment",
                    json={
                        "price_amount": amount,
                        "price_currency": "usd",
                        "pay_currency": "usdttrc20",
                        "order_id": f"sub_{user_id}_{strategy_id}_{int(datetime.now(timezone.utc).timestamp())}",
                        "order_description": f"strategy {strategy_id} - {plan_type}",
                        "ipn_callback_url": "https://your-domain.com/api/payments/nowpayments/callback",
                    },
                    headers={"x-api-key": settings.NOWPAYMENTS_API_KEY},
                )
                return response.json()
            except Exception:
                return self.get_manual_payment_details(amount)

    def get_manual_payment_details(self, amount: float) -> dict:
        return {
            "payment_method": "manual",
            "pay_address": settings.MANUAL_PAYMENT_ADDRESS,
            "payment_network": settings.MANUAL_PAYMENT_NETWORK,
            "pay_amount": amount,
            "payment_note": "Pay the exact amount, then submit the TxHash for admin review.",
        }
