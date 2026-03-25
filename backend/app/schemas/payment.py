"""
Payment schemas.
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class PaymentMethod(str, Enum):
    NOWPAYMENTS = "nowpayments"
    MANUAL_WALLET = "manual_wallet"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class PaymentCreate(BaseModel):
    strategy_id: int = Field(..., description="strategy id")
    plan_type: str = Field(..., description="monthly/yearly")


class PaymentVerify(BaseModel):
    tx_hash: str = Field(..., min_length=10, max_length=100)


class PaymentResponse(BaseModel):
    id: str
    user_id: int
    subscription_id: Optional[str] = None
    amount: Decimal
    payment_method: PaymentMethod
    tx_hash: Optional[str] = None
    status: PaymentStatus
    paid_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    created_at: datetime
    pay_address: Optional[str] = None
    payment_network: Optional[str] = None
    payment_note: Optional[str] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_payment(cls, payment, **extra_fields) -> "PaymentResponse":
        payload = {
            "id": payment.id,
            "user_id": payment.user_id,
            "subscription_id": payment.subscription_id,
            "amount": payment.amount,
            "payment_method": getattr(payment.payment_method, "value", payment.payment_method),
            "tx_hash": payment.tx_hash,
            "status": getattr(payment.status, "value", payment.status),
            "paid_at": payment.paid_at,
            "verified_at": payment.verified_at,
            "created_at": payment.created_at,
        }
        payload.update(extra_fields)
        return cls(**payload)


class NowPaymentsResponse(BaseModel):
    payment_id: int
    pay_address: str
    pay_amount: Decimal
    qr_code: Optional[str] = None
