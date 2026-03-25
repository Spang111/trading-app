"""
User routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.services.user_service import UserService


router = APIRouter()


@router.get("/profile", response_model=UserResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return UserResponse.from_user(current_user)


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_service = UserService(db)

    if user_in.username and user_in.username != current_user.username:
        existing_user = await user_service.get_by_username(user_in.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username is already in use.",
            )

    if user_in.email and user_in.email != current_user.email:
        existing_email = await user_service.get_by_email(user_in.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already registered.",
            )

    user = await user_service.update(current_user, user_in)
    return UserResponse.from_user(user)


@router.put("/wallet", response_model=UserResponse)
async def update_wallet(
    wallet_address: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_service = UserService(db)
    user_in = UserUpdate(wallet_address=wallet_address)
    user = await user_service.update(current_user, user_in)
    return UserResponse.from_user(user)
