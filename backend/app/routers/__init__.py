"""
API routers registry.
"""
from fastapi import APIRouter

from .admin import router as admin_router
from .auth import router as auth_router
from .exchanges import router as exchanges_router
from .payments import router as payments_router
from .signals import router as signals_router
from .stats import router as stats_router
from .strategies import router as strategies_router
from .subscriptions import router as subscriptions_router
from .users import router as users_router
from .webhook import router as webhook_router


api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(strategies_router, prefix="/strategies", tags=["strategies"])
api_router.include_router(payments_router, prefix="/payments", tags=["payments"])
api_router.include_router(subscriptions_router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(exchanges_router, prefix="/exchanges", tags=["exchanges"])
api_router.include_router(webhook_router, prefix="/webhook", tags=["webhook"])
api_router.include_router(signals_router, prefix="/signals", tags=["signals"])
api_router.include_router(stats_router, prefix="/stats", tags=["stats"])
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])

__all__ = ["api_router"]
