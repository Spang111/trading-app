"""
交易所 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.services.exchange_service import ExchangeService
from app.schemas.exchange import ExchangeAPICreate, ExchangeAPIResponse, ExchangeAPIVerify
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/apis", response_model=List[ExchangeAPIResponse])
async def get_exchange_apis(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户绑定的交易所 API 列表"""
    exchange_service = ExchangeService(db)
    apis = await exchange_service.get_user_apis(current_user.id)
    return apis


@router.post("/apis", response_model=ExchangeAPIResponse)
async def create_exchange_api(
    api_in: ExchangeAPICreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """绑定交易所 API"""
    exchange_service = ExchangeService(db)
    
    # 检查用户是否已绑定此交易所
    existing_apis = await exchange_service.get_user_apis(current_user.id)
    if any(api.exchange == api_in.exchange for api in existing_apis):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"已绑定 {api_in.exchange.value} 交易所 API"
        )
    
    api = await exchange_service.create(current_user.id, api_in)
    
    # 返回时隐藏敏感信息
    return ExchangeAPIResponse(
        id=api.id,
        user_id=api.user_id,
        exchange=api.exchange,
        api_key=f"{api.api_key[:8]}***",  # 仅显示前缀
        is_active=api.is_active,
        last_verified_at=api.last_verified_at,
        created_at=api.created_at,
        updated_at=api.updated_at,
    )


@router.post("/apis/{api_id}/verify")
async def verify_exchange_api(
    api_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """验证交易所 API 连接"""
    exchange_service = ExchangeService(db)
    api = await exchange_service.get_by_id(api_id)
    
    if not api:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="交易所 API 不存在"
        )
    
    if api.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此 API"
        )
    
    result = await exchange_service.verify_connection(api)
    
    if result.get("success"):
        # 更新最后验证时间
        from datetime import datetime, timezone
        api.last_verified_at = datetime.now(timezone.utc)
        await db.flush()
        
        return {"message": "连接成功", "details": result}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"连接失败：{result.get('error')}"
        )


@router.delete("/apis/{api_id}")
async def delete_exchange_api(
    api_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除交易所 API"""
    exchange_service = ExchangeService(db)
    api = await exchange_service.get_by_id(api_id)
    
    if not api:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="交易所 API 不存在"
        )
    
    if api.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此 API"
        )
    
    await exchange_service.delete(api)
    return {"message": "API 已删除"}
