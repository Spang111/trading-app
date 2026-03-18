"""
交易所 API 服务
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from app.models.exchange import ExchangeAPI, Exchange
from app.schemas.exchange import ExchangeAPICreate, ExchangeAPIVerify
from app.config import settings
from app.utils.security import encrypt_api_key, decrypt_api_key
import ccxt.async_support as ccxt


class ExchangeService:
    """交易所服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    def _proxy_url(self) -> Optional[str]:
        proxy = settings.PROXY_URL
        if proxy is None:
            return None
        if not isinstance(proxy, str):
            proxy = str(proxy)
        proxy = proxy.strip()
        return proxy or None

    def _with_proxy(self, config: dict) -> dict:
        proxy_url = self._proxy_url()
        if not proxy_url:
            return config
        config = dict(config)
        config["proxies"] = {"http": proxy_url, "https": proxy_url}
        return config
    
    async def get_by_id(self, api_id: str) -> Optional[ExchangeAPI]:
        """通过 ID 获取交易所 API"""
        return await self.db.get(ExchangeAPI, api_id)
    
    async def get_user_apis(self, user_id: int) -> List[ExchangeAPI]:
        """获取用户的交易所 API 列表"""
        result = await self.db.execute(
            select(ExchangeAPI)
            .where(ExchangeAPI.user_id == user_id)
            .where(ExchangeAPI.is_active == True)
        )
        return result.scalars().all()
    
    async def create(self, user_id: int, api_in: ExchangeAPICreate) -> ExchangeAPI:
        """创建交易所 API"""
        exchange_api = ExchangeAPI(
            user_id=user_id,
            exchange=api_in.exchange,
            api_key=encrypt_api_key(api_in.api_key),
            api_secret=encrypt_api_key(api_in.api_secret),
            passphrase=encrypt_api_key(api_in.passphrase) if api_in.passphrase else None,
        )
        self.db.add(exchange_api)
        await self.db.flush()
        await self.db.refresh(exchange_api)
        return exchange_api
    
    async def update(self, exchange_api: ExchangeAPI, api_in: ExchangeAPICreate) -> ExchangeAPI:
        """更新交易所 API"""
        exchange_api.exchange = api_in.exchange
        exchange_api.api_key = encrypt_api_key(api_in.api_key)
        exchange_api.api_secret = encrypt_api_key(api_in.api_secret)
        if api_in.passphrase:
            exchange_api.passphrase = encrypt_api_key(api_in.passphrase)
        
        await self.db.flush()
        await self.db.refresh(exchange_api)
        return exchange_api
    
    async def delete(self, exchange_api: ExchangeAPI) -> None:
        """删除交易所 API"""
        exchange_api.is_active = False
        await self.db.flush()
    
    async def verify_connection(
        self, 
        exchange_api: ExchangeAPI
    ) -> dict:
        """验证交易所连接"""
        api_key = decrypt_api_key(exchange_api.api_key)
        api_secret = decrypt_api_key(exchange_api.api_secret)
        passphrase = decrypt_api_key(exchange_api.passphrase) if exchange_api.passphrase else None
        exchange = None
        try:
            if exchange_api.exchange == Exchange.OKX:
                exchange = ccxt.okx(self._with_proxy({
                    'apiKey': api_key,
                    'secret': api_secret,
                    'password': passphrase,
                    'enableRateLimit': True,
                    'timeout': 30000,
                }))
            elif exchange_api.exchange == Exchange.BINANCE:
                exchange = ccxt.binance(self._with_proxy({
                    'apiKey': api_key,
                    'secret': api_secret,
                    'enableRateLimit': True,
                    'timeout': 30000,
                }))
            else:
                return {"success": False, "error": "不支持的交易所"}
            
            # 测试连接
            await exchange.fetch_balance()
            
            return {"success": True, "message": "连接成功"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            if exchange is not None:
                try:
                    await exchange.close()
                except Exception:
                    pass
    
    async def place_order(
        self,
        exchange_api: ExchangeAPI,
        symbol: str,
        order_type: str,
        side: str,
        amount: float,
        price: Optional[float] = None,
        leverage: Optional[int] = None,
    ) -> dict:
        """下单"""
        api_key = decrypt_api_key(exchange_api.api_key)
        api_secret = decrypt_api_key(exchange_api.api_secret)
        passphrase = decrypt_api_key(exchange_api.passphrase) if exchange_api.passphrase else None
        exchange = None
        try:
            if exchange_api.exchange == Exchange.OKX:
                exchange = ccxt.okx(self._with_proxy({
                    'apiKey': api_key,
                    'secret': api_secret,
                    'password': passphrase,
                    'enableRateLimit': True,
                    'timeout': 30000,
                }))
            elif exchange_api.exchange == Exchange.BINANCE:
                exchange = ccxt.binance(self._with_proxy({
                    'apiKey': api_key,
                    'secret': api_secret,
                    'enableRateLimit': True,
                    'timeout': 30000,
                }))
            else:
                return {"success": False, "error": "不支持的交易所"}
            
            # 设置杠杆
            if leverage:
                await exchange.set_leverage(leverage, symbol)
            
            # 下单
            if order_type == "market":
                order = await exchange.create_market_order(symbol, side, amount)
            else:
                order = await exchange.create_limit_order(symbol, side, amount, price)
            
            return {
                "success": True,
                "order_id": order['id'],
                "status": order['status'],
                "price": order.get('price'),
                "amount": order.get('amount'),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            if exchange is not None:
                try:
                    await exchange.close()
                except Exception:
                    pass
