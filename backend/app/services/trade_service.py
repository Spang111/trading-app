"""
Trade execution engine with concurrency control and exchange market cache.
"""
import asyncio
import enum
import logging
from decimal import Decimal, ROUND_DOWN
from typing import Any, Dict, List, Optional

import ccxt.async_support as ccxt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session_maker
from app.models.exchange import Exchange, ExchangeAPI
from app.models.signal import (
    ExecutionStatus,
    OrderType,
    SignalAction,
    SignalSource,
    SignalStatus,
    TradingSignal,
    SignalExecution,
)
from app.models.strategy import StrategySubscription, SubscriptionStatus
from app.utils.security import decrypt_api_key


logger = logging.getLogger(__name__)

# Global exchange market cache (filled at app startup)
EXCHANGE_MARKETS_CACHE: Dict[str, Dict[str, Any]] = {}
EXCHANGE_WARMUP_LOCKS: Dict[str, asyncio.Lock] = {}

# Concurrency limiter for order placement
ORDER_SEMAPHORE = asyncio.Semaphore(5)


def _proxy_url() -> Optional[str]:
    proxy = settings.PROXY_URL
    if proxy is None:
        return None
    if not isinstance(proxy, str):
        proxy = str(proxy)
    proxy = proxy.strip()
    return proxy or None


def _with_proxy(config: Dict[str, Any]) -> Dict[str, Any]:
    proxy_url = _proxy_url()
    if not proxy_url:
        return config
    config = dict(config)
    config["proxies"] = {"http": proxy_url, "https": proxy_url}
    return config


async def _close_exchange(exchange: Optional[ccxt.Exchange]) -> None:
    if exchange is None:
        return

    try:
        await exchange.close()
    except Exception as exc:
        logger.debug(
            "[exchange-close] exchange=%s failed: %s",
            getattr(exchange, "id", "unknown"),
            exc,
        )


def _get_exchange_warmup_lock(exchange_id: str) -> asyncio.Lock:
    lock = EXCHANGE_WARMUP_LOCKS.get(exchange_id)
    if lock is None:
        lock = asyncio.Lock()
        EXCHANGE_WARMUP_LOCKS[exchange_id] = lock
    return lock


def _warmup_default_type(exchange_id: str) -> str:
    if exchange_id == "binance":
        return "future"
    return "swap"


def _select_derivative_markets(
    exchange: ccxt.Exchange,
    symbol_filter: Optional[set[str]] = None,
) -> Dict[str, Dict[str, Any]]:
    markets = getattr(exchange, "markets", {}) or {}
    selected: Dict[str, Dict[str, Any]] = {}

    for symbol, market in markets.items():
        if not symbol or not isinstance(market, dict):
            continue
        if market.get("active") is False:
            continue

        market_type = str(market.get("type") or "").lower()
        is_derivative = bool(
            market.get("swap")
            or market.get("future")
            or market.get("contract")
            or market_type in {"swap", "future"}
        )
        if not is_derivative:
            continue

        if symbol_filter and symbol not in symbol_filter:
            continue

        selected[symbol] = market

    return selected


def cache_exchange_markets(
    exchange_id: str,
    markets: Dict[str, Any],
    markets_by_id: Optional[Dict[str, Any]] = None,
    symbols: Optional[List[str]] = None,
    currencies: Optional[Dict[str, Any]] = None,
) -> None:
    if markets_by_id is None:
        markets_by_id = {m.get("id"): m for m in markets.values() if isinstance(m, dict)}
    if symbols is None:
        symbols = list(markets.keys())

    EXCHANGE_MARKETS_CACHE[exchange_id] = {
        "markets": markets,
        "markets_by_id": markets_by_id,
        "symbols": symbols,
        "currencies": currencies or {},
    }


async def warmup_exchange_markets(exchange_ids: List[str]) -> None:
    for exchange_id in exchange_ids:
        exchange_id = exchange_id.strip().lower()
        await _warmup_exchange(exchange_id)


async def _warmup_exchange(exchange_id: str) -> bool:
    exchange_id = exchange_id.strip().lower()
    if not exchange_id:
        return False
    if not hasattr(ccxt, exchange_id):
        logger.warning("[warmup] exchange=%s is not supported by ccxt", exchange_id)
        return False

    lock = _get_exchange_warmup_lock(exchange_id)
    async with lock:
        if EXCHANGE_MARKETS_CACHE.get(exchange_id):
            return True

        exchange_class = getattr(ccxt, exchange_id)
        exchange_config = {"enableRateLimit": True, "timeout": 30000}
        exchange: Optional[ccxt.Exchange] = exchange_class(_with_proxy(exchange_config))
        try:
            exchange.options["defaultType"] = _warmup_default_type(exchange_id)
            await exchange.load_markets(reload=True)

            monitored_symbols = {
                str(symbol).strip()
                for symbol in (settings.MONITOR_SYMBOLS or [])
                if str(symbol).strip()
            }
            derivative_markets = _select_derivative_markets(exchange)
            markets = _select_derivative_markets(exchange, symbol_filter=monitored_symbols)

            if monitored_symbols and not markets and derivative_markets:
                logger.warning(
                    "[warmup] exchange=%s monitor symbols not found; caching all derivative markets instead",
                    exchange_id,
                )
                markets = derivative_markets
            elif not monitored_symbols:
                markets = derivative_markets

            if not markets:
                logger.warning("[warmup] exchange=%s loaded no derivative markets", exchange_id)
                return False

            cache_exchange_markets(
                exchange_id,
                markets=markets,
                markets_by_id={m.get("id"): m for m in markets.values() if m.get("id")},
                symbols=list(markets.keys()),
                currencies=getattr(exchange, "currencies", None),
            )
            logger.info("[warmup] exchange=%s cached %d derivative markets", exchange_id, len(markets))
            return True
        except Exception as exc:
            logger.warning("[warmup] exchange=%s failed: %s", exchange_id, exc)
            return False
        finally:
            await _close_exchange(exchange)


def _apply_market_cache(exchange_id: str, exchange: ccxt.Exchange) -> None:
    cache = EXCHANGE_MARKETS_CACHE.get(exchange_id)
    if not cache:
        return
    exchange.markets = cache.get("markets", {})
    exchange.markets_by_id = cache.get("markets_by_id", {})
    exchange.symbols = cache.get("symbols", [])
    exchange.currencies = cache.get("currencies", {})


def _resolve_symbol(exchange_id: str, raw_symbol: str) -> str:
    cache = EXCHANGE_MARKETS_CACHE.get(exchange_id, {})
    markets = cache.get("markets", {})
    markets_by_id = cache.get("markets_by_id", {})

    if raw_symbol in markets:
        return raw_symbol
    if raw_symbol in markets_by_id:
        return markets_by_id[raw_symbol].get("symbol", raw_symbol)
    return raw_symbol


def _round_down(value: Decimal, precision: Optional[int]) -> Decimal:
    if precision is None:
        return value
    quant = Decimal("1").scaleb(-precision)
    return value.quantize(quant, rounding=ROUND_DOWN)


def _get_amount_precision(exchange_id: str, symbol: str) -> Optional[int]:
    cache = EXCHANGE_MARKETS_CACHE.get(exchange_id, {})
    market = cache.get("markets", {}).get(symbol)
    if not market:
        return None
    precision = market.get("precision", {})
    return precision.get("amount")


def _get_price_precision(exchange_id: str, symbol: str) -> Optional[int]:
    cache = EXCHANGE_MARKETS_CACHE.get(exchange_id, {})
    market = cache.get("markets", {}).get(symbol)
    if not market:
        return None
    precision = market.get("precision", {})
    return precision.get("price")


async def execute_trade_signal(
    signal_data: Dict[str, Any],
    db: Optional[AsyncSession] = None,
) -> Dict[str, Any]:
    if db is None:
        async with async_session_maker() as session:
            return await _execute_trade_signal_with_session(signal_data, session)
    return await _execute_trade_signal_with_session(signal_data, db)


async def _execute_trade_signal_with_session(
    signal_data: Dict[str, Any],
    db: AsyncSession,
) -> Dict[str, Any]:
    action_value = signal_data["action"]
    if isinstance(action_value, enum.Enum):
        action_value = action_value.value
    order_type_value = signal_data["order_type"]
    if isinstance(order_type_value, enum.Enum):
        order_type_value = order_type_value.value
    source_value = signal_data.get("source", SignalSource.TRADINGVIEW)
    if isinstance(source_value, enum.Enum):
        source_value = source_value.value

    try:
        signal = TradingSignal(
            strategy_id=signal_data["strategy_id"],
            source=SignalSource(source_value),
            action=SignalAction(action_value),
            ticker=signal_data["ticker"],
            order_type=OrderType(order_type_value),
            quantity=signal_data["quantity"],
            price=signal_data.get("price"),
            leverage=signal_data.get("leverage"),
            exchange=str(signal_data["exchange"]).lower(),
            raw_payload=signal_data.get("raw_payload"),
            status=SignalStatus.PENDING,
        )
        db.add(signal)
        await db.flush()
        await db.refresh(signal)

        signal.status = SignalStatus.PROCESSING
        await db.flush()

        subscriptions = await _get_active_subscriptions(db, signal.strategy_id)
        if not subscriptions:
            signal.status = SignalStatus.COMPLETED
            await db.flush()
            await db.commit()
            return {"signal_id": signal.id, "total": 0, "success": 0, "failed": 0}

        results: List[Dict[str, Any]] = []

        subscription_refs = [(sub.id, int(sub.user_id)) for sub in subscriptions]

        async def _run_for_subscription(subscription_id: str, user_id: int) -> Dict[str, Any]:
            # Each task uses its own DB session; AsyncSession is not safe to share concurrently.
            async with ORDER_SEMAPHORE:
                async with async_session_maker() as task_db:
                    return await _execute_order_for_user(
                        task_db,
                        subscription_id=subscription_id,
                        user_id=user_id,
                        signal=signal,
                    )

        tasks: List[asyncio.Task] = []
        task_meta: Dict[asyncio.Task, tuple[str, int]] = {}
        for subscription_id, user_id in subscription_refs:
            # 平滑限频：每遍历一个用户都短暂休眠，避免瞬时突发请求
            await asyncio.sleep(0.05)
            task = asyncio.create_task(_run_for_subscription(subscription_id, user_id))
            tasks.append(task)
            task_meta[task] = (subscription_id, user_id)

        for task in asyncio.as_completed(tasks):
            try:
                results.append(await task)
            except Exception as exc:
                meta = task_meta.get(task)
                if meta is None:
                    logger.exception("Order task failed (missing metadata): %s", exc)
                    continue
                subscription_id, user_id = meta
                results.append(
                    {
                        "user_id": user_id,
                        "subscription_id": subscription_id,
                        "exchange_api_id": None,
                        "status": "failed",
                        "error": str(exc),
                    }
                )

        await _save_execution_results(db, signal.id, results)
        signal.status = SignalStatus.COMPLETED
        await db.flush()
        await db.commit()

        success_count = sum(1 for r in results if r.get("status") == "success")
        failed_count = sum(1 for r in results if r.get("status") != "success")
        return {
            "signal_id": signal.id,
            "total": len(results),
            "success": success_count,
            "failed": failed_count,
        }
    except Exception:
        await db.rollback()
        raise


async def _get_active_subscriptions(
    db: AsyncSession,
    strategy_id: str,
) -> List[StrategySubscription]:
    result = await db.execute(
        select(StrategySubscription)
        .where(StrategySubscription.strategy_id == strategy_id)
        .where(StrategySubscription.status == SubscriptionStatus.ACTIVE)
    )
    return result.scalars().all()


async def _get_user_exchange_api(
    db: AsyncSession,
    user_id: int,
    exchange: str,
) -> Optional[ExchangeAPI]:
    try:
        exchange_value: Exchange | str = Exchange(exchange)
    except Exception:
        exchange_value = exchange
    result = await db.execute(
        select(ExchangeAPI)
        .where(ExchangeAPI.user_id == user_id)
        .where(ExchangeAPI.exchange == exchange_value)
        .where(ExchangeAPI.is_active == True)
    )
    return result.scalar_one_or_none()


async def _execute_order_for_user(
    db: AsyncSession,
    *,
    subscription_id: str,
    user_id: int,
    signal: TradingSignal,
) -> Dict[str, Any]:
    exchange_id = signal.exchange.lower()
    exchange_api = await _get_user_exchange_api(db, user_id, exchange_id)
    if not exchange_api:
        return {
            "user_id": user_id,
            "subscription_id": subscription_id,
            "exchange_api_id": None,
            "status": "failed",
            "error": "missing_exchange_api",
        }
    exchange_api_id = exchange_api.id

    api_key = decrypt_api_key(exchange_api.api_key)
    api_secret = decrypt_api_key(exchange_api.api_secret)
    passphrase = decrypt_api_key(exchange_api.passphrase) if exchange_api.passphrase else None

    exchange_class = getattr(ccxt, exchange_id, None)
    if exchange_class is None:
        return {
            "user_id": user_id,
            "subscription_id": subscription_id,
            "exchange_api_id": exchange_api_id,
            "status": "failed",
            "error": "unsupported_exchange",
        }

    params: Dict[str, Any] = {
        "apiKey": api_key,
        "secret": api_secret,
        "enableRateLimit": True,
        "timeout": 30000,
    }
    if exchange_id == Exchange.OKX.value and passphrase:
        params["password"] = passphrase
    params = _with_proxy(params)

    exchange = exchange_class(params)
    try:
        # Apply preloaded markets to avoid load_markets in the order path
        if exchange_id not in EXCHANGE_MARKETS_CACHE:
            await _warmup_exchange(exchange_id)
        if exchange_id not in EXCHANGE_MARKETS_CACHE:
            return {
                "user_id": user_id,
                "subscription_id": subscription_id,
                "exchange_api_id": exchange_api_id,
                "status": "failed",
                "error": "market_cache_missing",
            }
        _apply_market_cache(exchange_id, exchange)

        symbol = _resolve_symbol(exchange_id, signal.ticker)
        if symbol not in EXCHANGE_MARKETS_CACHE.get(exchange_id, {}).get("markets", {}):
            return {
                "user_id": user_id,
                "subscription_id": subscription_id,
                "exchange_api_id": exchange_api_id,
                "status": "failed",
                "error": "symbol_not_found",
            }
        amount = Decimal(str(signal.quantity))
        amount_precision = _get_amount_precision(exchange_id, symbol)
        safe_amount = _round_down(amount, amount_precision)

        price = None
        if signal.price is not None:
            price_val = Decimal(str(signal.price))
            price_precision = _get_price_precision(exchange_id, symbol)
            price = _round_down(price_val, price_precision)

        if signal.leverage:
            try:
                await exchange.set_leverage(signal.leverage, symbol)
            except Exception:
                pass

        if signal.order_type.value == "market":
            order = await exchange.create_market_order(symbol, signal.action.value, float(safe_amount))
        else:
            order = await exchange.create_limit_order(
                symbol,
                signal.action.value,
                float(safe_amount),
                float(price) if price is not None else None,
            )

        return {
            "user_id": user_id,
            "subscription_id": subscription_id,
            "exchange_api_id": exchange_api_id,
            "status": "success",
            "order_id": order.get("id"),
            "executed_price": order.get("price"),
            "executed_quantity": order.get("amount"),
        }
    except Exception as exc:
        return {
            "user_id": user_id,
            "subscription_id": subscription_id,
            "exchange_api_id": exchange_api_id,
            "status": "failed",
            "error": str(exc),
        }
    finally:
        await _close_exchange(exchange)


async def _save_execution_results(
    db: AsyncSession,
    signal_id: str,
    results: List[Dict[str, Any]],
) -> None:
    executions: List[SignalExecution] = []
    for result in results:
        user_id = result.get("user_id")
        if user_id is None:
            continue
        status = ExecutionStatus.SUCCESS if result.get("status") == "success" else ExecutionStatus.FAILED
        executions.append(
            SignalExecution(
                signal_id=signal_id,
                user_id=user_id,
                subscription_id=result.get("subscription_id"),
                exchange_api_id=result.get("exchange_api_id"),
                execution_status=status,
                order_id=result.get("order_id"),
                executed_price=result.get("executed_price"),
                executed_quantity=result.get("executed_quantity"),
                error_message=result.get("error"),
            )
        )

    if executions:
        db.add_all(executions)
        await db.flush()
