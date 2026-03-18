"""
信号路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.services.signal_service import SignalService
from app.schemas.signal import SignalResponse, SignalExecutionResponse
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("", response_model=List[SignalResponse])
async def get_signals(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户的信号日志"""
    signal_service = SignalService(db)
    signals = await signal_service.get_user_signals(
        current_user.id,
        skip=skip,
        limit=limit
    )
    return signals


@router.get("/recent", response_model=List[SignalResponse])
async def get_recent_signals(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """获取最近的信号（公开，用于首页展示）"""
    signal_service = SignalService(db)
    signals = await signal_service.get_recent_signals(limit=limit)
    return signals


@router.get("/{signal_id}", response_model=SignalResponse)
async def get_signal(
    signal_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取信号详情"""
    signal_service = SignalService(db)
    signal = await signal_service.get_user_signals(current_user.id)
    
    signal_obj = next((s for s in signal if s.id == signal_id), None)
    if not signal_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="信号不存在"
        )
    
    return signal_obj


@router.get("/{signal_id}/executions", response_model=List[SignalExecutionResponse])
async def get_signal_executions(
    signal_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取信号执行记录"""
    signal_service = SignalService(db)
    signal = await signal_service.get_user_signals(current_user.id)
    
    signal_obj = next((s for s in signal if s.id == signal_id), None)
    if not signal_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="信号不存在"
        )
    
    # 获取执行记录
    executions = signal_obj.executions
    return executions
