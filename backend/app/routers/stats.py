"""
统计路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.stats_service import StatsService
from app.schemas.stats import PlatformStatsResponse, UserStatsResponse
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/platform", response_model=PlatformStatsResponse)
async def get_platform_stats(
    db: AsyncSession = Depends(get_db)
):
    """获取平台统计数据"""
    stats_service = StatsService(db)
    stats = await stats_service.get_platform_stats()
    return stats


@router.get("/user", response_model=UserStatsResponse)
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户个人统计"""
    stats_service = StatsService(db)
    stats = await stats_service.get_user_stats(current_user.id)
    return stats
