"""
Webhook 配置服务
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
import json
from app.models.webhook import WebhookConfig
from app.utils.webhook_security import generate_secret_key


class WebhookService:
    """Webhook 配置服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, config_id: str) -> Optional[WebhookConfig]:
        """通过 ID 获取 Webhook 配置"""
        return await self.db.get(WebhookConfig, config_id)
    
    async def get_user_config(self, user_id: int, strategy_id: int) -> Optional[WebhookConfig]:
        """获取用户的 Webhook 配置"""
        result = await self.db.execute(
            select(WebhookConfig)
            .where(WebhookConfig.user_id == user_id)
            .where(WebhookConfig.strategy_id == strategy_id)
            .where(WebhookConfig.is_active == True)
        )
        return result.scalar_one_or_none()
    
    async def create_or_update(
        self, 
        user_id: int, 
        strategy_id: int,
        allowed_ips: Optional[List[str]] = None
    ) -> WebhookConfig:
        """创建或更新 Webhook 配置"""
        # 检查是否已存在
        existing = await self.get_user_config(user_id, strategy_id)
        
        if existing:
            # 更新现有配置
            if allowed_ips:
                existing.allowed_ips = json.dumps(allowed_ips)
            await self.db.flush()
            await self.db.refresh(existing)
            return existing
        
        # 创建新配置
        secret_key = generate_secret_key()
        webhook_url = f"https://your-domain.com/api/webhook/receive?key={secret_key}"
        
        config = WebhookConfig(
            user_id=user_id,
            strategy_id=strategy_id,
            webhook_url=webhook_url,
            secret_key=secret_key,
            allowed_ips=json.dumps(allowed_ips) if allowed_ips else None,
        )
        
        self.db.add(config)
        await self.db.flush()
        await self.db.refresh(config)
        return config
    
    async def get_allowed_ips(self, config: WebhookConfig) -> List[str]:
        """获取允许的 IP 列表"""
        if config.allowed_ips:
            return json.loads(config.allowed_ips)
        return []
