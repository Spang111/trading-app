"""
Admin routes.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_admin_user
from app.models.signal import SignalSource
from app.schemas.admin import ManualTradePayload
from app.services.trade_service import execute_trade_signal


router = APIRouter()


@router.post("/manual-trade")
async def manual_trade(
    payload: ManualTradePayload,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_current_admin_user),
):
    signal_data = {
        "strategy_id": payload.strategy_id,
        "source": SignalSource.ADMIN_MANUAL,
        "action": payload.action,
        "ticker": payload.ticker,
        "order_type": payload.order_type,
        "quantity": payload.quantity,
        "price": payload.price,
        "leverage": payload.leverage,
        "exchange": payload.exchange,
        "raw_payload": payload.model_dump(),
    }

    result = await execute_trade_signal(signal_data, db=db)
    return {"status": "submitted", "result": result}
