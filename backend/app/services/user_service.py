"""
用户服务
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from app.models.user import User, UserRole, UserStatus
from app.utils.security import hash_password, verify_password
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """用户服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """通过 ID 获取用户"""
        return await self.db.get(User, user_id)
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """通过用户名获取用户"""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """通过邮箱获取用户"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def create(self, user_in: UserCreate) -> User:
        """创建用户"""
        user = User(
            username=user_in.username,
            email=user_in.email,
            password_hash=hash_password(user_in.password),
            wallet_address=user_in.wallet_address,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user
    
    async def update(self, user: User, user_in: UserUpdate) -> User:
        """更新用户"""
        update_data = user_in.model_dump(exclude_unset=True)
        
        if "password" in update_data:
            update_data["password_hash"] = hash_password(update_data.pop("password"))
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        await self.db.flush()
        await self.db.refresh(user)
        return user
    
    async def authenticate(self, username: str, password: str) -> Optional[User]:
        """用户认证"""
        user = await self.get_by_username(username)
        if not user:
            user = await self.get_by_email(username)
        
        if not user:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        return user
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """获取所有用户"""
        result = await self.db.execute(
            select(User).offset(skip).limit(limit)
        )
        return result.scalars().all()
