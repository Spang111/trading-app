"""
TradingView webhook endpoint.
"""
import json

from fastapi import APIRouter, HTTPException, Request, status

from app.config import settings
from app.models.signal import SignalSource
from app.schemas.webhook import WebhookPayload
from app.services.trade_service import execute_trade_signal
from app.utils.ip import get_client_ip
from app.utils.webhook_security import verify_webhook_ip, verify_webhook_signature


router = APIRouter()


@router.post("/receive")
async def receive_webhook(request: Request):
    # 1) IP whitelist
    client_ip = get_client_ip(request)
    if not verify_webhook_ip(client_ip):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"IP {client_ip} is not allowed",
        )

    # 2) Parse payload
    body_bytes = await request.body()
    try:
        payload_data = json.loads(body_bytes.decode("utf-8"))
        payload = WebhookPayload(**payload_data)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid payload: {exc}",
        )

    if not payload.strategy_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="strategy_id is required",
        )

    # 3) Secret validation (passphrase + optional signature)
    if payload.passphrase != settings.TRADINGVIEW_PASSPHRASE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid passphrase",
        )

    signature = request.headers.get("X-Signature")
    if signature and not verify_webhook_signature(
        body_bytes.decode("utf-8"),
        settings.TRADINGVIEW_PASSPHRASE,
        signature,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid signature",
        )

    signal_data = {
        "strategy_id": payload.strategy_id,
        "source": SignalSource.TRADINGVIEW,
        "action": payload.action,
        "ticker": payload.ticker,
        "order_type": payload.order_type,
        "quantity": payload.quantity,
        "price": payload.price,
        "leverage": payload.leverage,
        "exchange": payload.exchange,
        "raw_payload": payload.model_dump(),
    }

    # fire-and-forget async execution (tracked for graceful shutdown)
    task_manager = getattr(request.app.state, "task_manager", None)
    if task_manager is not None:
        task_manager.create_task(execute_trade_signal(signal_data), name="execute_trade_signal")
    else:
        # Fallback: create task without tracking (should not happen in prod).
        import asyncio

        asyncio.create_task(execute_trade_signal(signal_data))

    return {"status": "received"}
