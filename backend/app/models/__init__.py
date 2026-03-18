"""
数据库模型初始化
"""
from .user import User
from .strategy import Strategy, SubscriptionPlan, StrategySubscription
from .payment import Payment
from .exchange import ExchangeAPI
from .webhook import WebhookConfig
from .signal import TradingSignal, SignalExecution
from .profit_sharing import ProfitSharingRule, ProfitSharingRecord
from .stats import SystemStats

__all__ = [
    "User",
    "Strategy",
    "SubscriptionPlan",
    "StrategySubscription",
    "Payment",
    "ExchangeAPI",
    "WebhookConfig",
    "TradingSignal",
    "SignalExecution",
    "ProfitSharingRule",
    "ProfitSharingRecord",
    "SystemStats",
]
