"""
Strategy routes.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_admin_user
from app.models.user import User
from app.schemas.strategy import (
    StrategyCreate,
    StrategyResponse,
    StrategyUpdate,
    SubscriptionPlanResponse,
)
from app.services.strategy_service import StrategyService


router = APIRouter()


@router.get("", response_model=List[StrategyResponse])
async def get_strategies(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """Return active marketplace strategies."""
    strategy_service = StrategyService(db)
    strategies = await strategy_service.get_all(skip=skip, limit=limit)
    return strategies


@router.get("/admin/list", response_model=List[StrategyResponse])
async def get_all_strategies_for_admin(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Return active and inactive strategies for admin management."""
    del current_user
    strategy_service = StrategyService(db)
    strategies = await strategy_service.get_all(
        skip=skip,
        limit=limit,
        include_inactive=True,
    )
    return strategies


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Return one strategy."""
    strategy_service = StrategyService(db)
    strategy = await strategy_service.get_by_id(strategy_id)

    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found.",
        )

    return strategy


@router.get("/{strategy_id}/plans", response_model=List[SubscriptionPlanResponse])
async def get_strategy_plans(
    strategy_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Return the active plans for one strategy."""
    strategy_service = StrategyService(db)
    plans = await strategy_service.get_plans(strategy_id)
    return plans


@router.post("", response_model=StrategyResponse)
async def create_strategy(
    strategy_in: StrategyCreate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a strategy (admin only)."""
    del current_user
    strategy_service = StrategyService(db)
    strategy = await strategy_service.create(strategy_in)
    return strategy


@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: int,
    strategy_in: StrategyUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a strategy (admin only)."""
    del current_user
    strategy_service = StrategyService(db)
    strategy = await strategy_service.get_by_id(strategy_id)

    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found.",
        )

    strategy = await strategy_service.update(strategy, strategy_in)
    return strategy
