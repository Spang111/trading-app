"""
用户路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.user_service import UserService
from app.schemas.user import UserResponse, UserUpdate
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/profile", response_model=UserResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户资料"""
    return current_user


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新用户资料"""
    user_service = UserService(db)
    
    # 检查新用户名是否已被使用
    if user_in.username and user_in.username != current_user.username:
        existing_user = await user_service.get_by_username(user_in.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已被使用"
            )
    
    # 检查新邮箱是否已被使用
    if user_in.email and user_in.email != current_user.email:
        existing_email = await user_service.get_by_email(user_in.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )
    
    # 更新用户
    user = await user_service.update(current_user, user_in)
    return user


@router.put("/wallet", response_model=UserResponse)
async def update_wallet(
    wallet_address: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新钱包地址"""
    user_service = UserService(db)
    user_in = UserUpdate(wallet_address=wallet_address)
    user = await user_service.update(current_user, user_in)
    return user
