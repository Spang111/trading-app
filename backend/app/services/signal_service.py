"""
信号处理服务（核心交易引擎）
"""
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Union, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.signal import TradingSignal, SignalExecution, SignalStatus, SignalAction, ExecutionStatus
from app.models.strategy import StrategySubscription, SubscriptionStatus
from app.models.exchange import ExchangeAPI
from app.schemas.webhook import WebhookPayload
from app.services.exchange_service import ExchangeService


class SignalService:
    """信号服务类（异步并发处理）"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_signal(self, payload: WebhookPayload, strategy_id: str) -> TradingSignal:
        """创建交易信号"""
        signal = TradingSignal(
            strategy_id=strategy_id,
            action=payload.action,
            ticker=payload.ticker,
            order_type=payload.order_type,
            quantity=payload.quantity,
            price=payload.price,
            leverage=payload.leverage,
            exchange=payload.exchange,
            raw_payload=payload.model_dump(),
            status=SignalStatus.PENDING,
        )
        self.db.add(signal)
        await self.db.flush()
        await self.db.refresh(signal)
        return signal
    
    async def process_signal_async(self, signal_id: str):
        """
        异步处理信号分发（核心防滑点逻辑）
        使用 asyncio.gather 实现并发下单
        """
        signal = await self.db.get(TradingSignal, signal_id)
        if not signal:
            return
        
        # 更新信号状态为处理中
        signal.status = SignalStatus.PROCESSING
        signal.processed_at = datetime.now(timezone.utc)
        await self.db.flush()
        
        # 获取所有订阅此策略的活跃用户
        subscriptions = await self._get_active_subscriptions(signal.strategy_id)
        
        if not subscriptions:
            signal.status = SignalStatus.COMPLETED
            await self.db.flush()
            return
        
        # 创建并发任务列表
        tasks = [
            self._execute_order_for_user(sub, signal)
            for sub in subscriptions
        ]
        
        # 并发执行所有下单任务（防滑点关键）
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 记录执行结果
        await self._save_execution_results(signal_id, results)
        
        # 更新信号状态
        signal.status = SignalStatus.COMPLETED
        await self.db.flush()
    
    async def _execute_order_for_user(
        self, 
        subscription: StrategySubscription, 
        signal: TradingSignal
    ) -> Dict[str, Any]:
        """为单个用户执行订单（异步）"""
        try:
            # 获取用户的交易所 API
            exchange_api = await self._get_user_exchange_api(
                subscription.user_id, 
                signal.exchange
            )
            
            if not exchange_api:
                return {
                    "user_id": subscription.user_id,
                    "status": "failed",
                    "error": "未绑定交易所 API"
                }
            
            # 使用 ExchangeService 下单
            exchange_service = ExchangeService(self.db)
            order_result = await exchange_service.place_order(
                exchange_api=exchange_api,
                symbol=signal.ticker.replace("/", ""),  # BTC/USDT -> BTCUSDT
                order_type=signal.order_type.value,
                side=signal.action.value,
                amount=float(signal.quantity),
                price=float(signal.price) if signal.price else None,
                leverage=signal.leverage,
            )
            
            if order_result.get("success"):
                return {
                    "user_id": subscription.user_id,
                    "status": "success",
                    "order_id": order_result.get("order_id"),
                    "executed_price": order_result.get("price"),
                    "executed_quantity": order_result.get("amount"),
                }
            else:
                return {
                    "user_id": subscription.user_id,
                    "status": "failed",
                    "error": order_result.get("error", "未知错误")
                }
        
        except Exception as e:
            return {
                "user_id": subscription.user_id,
                "status": "failed",
                "error": str(e)
            }
    
    async def _get_active_subscriptions(self, strategy_id: str) -> List[StrategySubscription]:
        """获取策略的所有活跃订阅"""
        result = await self.db.execute(
            select(StrategySubscription)
            .where(StrategySubscription.strategy_id == strategy_id)
            .where(StrategySubscription.status == SubscriptionStatus.ACTIVE)
        )
        return result.scalars().all()
    
    async def _get_user_exchange_api(self, user_id: str, exchange: str) -> Optional[ExchangeAPI]:
        """获取用户的交易所 API"""
        result = await self.db.execute(
            select(ExchangeAPI)
            .where(ExchangeAPI.user_id == user_id)
            .where(ExchangeAPI.exchange == exchange)
            .where(ExchangeAPI.is_active == True)
        )
        return result.scalar_one_or_none()
    
    async def _save_execution_results(self, signal_id: str, results: List[Dict[str, Any]]):
        """保存执行结果"""
        executions = []
        
        for result in results:
            if isinstance(result, Exception):
                continue
            
            execution = SignalExecution(
                signal_id=signal_id,
                user_id=result.get("user_id"),
                execution_status=ExecutionStatus.SUCCESS if result.get("status") == "success" else ExecutionStatus.FAILED,
                order_id=result.get("order_id"),
                executed_price=result.get("executed_price"),
                executed_quantity=result.get("executed_quantity"),
                error_message=result.get("error"),
            )
            executions.append(execution)
        
        if executions:
            self.db.add_all(executions)
            await self.db.flush()
    
    async def get_user_signals(
        self, 
        user_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[TradingSignal]:
        """获取用户的信号日志"""
        # 通过订阅关联查询信号
        result = await self.db.execute(
            select(TradingSignal)
            .join(StrategySubscription, TradingSignal.strategy_id == StrategySubscription.strategy_id)
            .where(StrategySubscription.user_id == user_id)
            .order_by(TradingSignal.received_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_recent_signals(self, limit: int = 10) -> List[TradingSignal]:
        """获取最近的信号（公开，用于首页展示）"""
        result = await self.db.execute(
            select(TradingSignal)
            .where(TradingSignal.status == SignalStatus.COMPLETED)
            .order_by(TradingSignal.received_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
