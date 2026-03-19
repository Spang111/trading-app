"""
User service helpers.
"""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.utils.security import hash_password, verify_password


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> Optional[User]:
        return await self.db.get(User, user_id)

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, user_in: UserCreate) -> User:
        verified_now = not settings.EMAIL_VERIFICATION_REQUIRED
        verification_time = self.utcnow() if verified_now else None

        user = User(
            username=user_in.username,
            email=user_in.email,
            password_hash=hash_password(user_in.password),
            wallet_address=user_in.wallet_address,
            email_verified=verified_now,
            email_verified_at=verification_time,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update(self, user: User, user_in: UserUpdate) -> User:
        update_data = user_in.model_dump(exclude_unset=True)

        if "password" in update_data:
            update_data["password_hash"] = hash_password(update_data.pop("password"))

        for field, value in update_data.items():
            setattr(user, field, value)

        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def authenticate(self, username: str, password: str) -> Optional[User]:
        user = await self.get_by_username(username)
        if user is None:
            user = await self.get_by_email(username)

        if user is None:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user

    async def mark_verification_email_sent(self, user: User) -> User:
        user.email_verification_sent_at = self.utcnow()
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def verify_email(self, user: User) -> User:
        now = self.utcnow()
        user.email_verified = True
        user.email_verified_at = now
        user.email_verification_sent_at = now
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def set_password(self, user: User, password: str) -> User:
        user.password_hash = hash_password(password)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        result = await self.db.execute(select(User).offset(skip).limit(limit))
        return list(result.scalars().all())

    @staticmethod
    def utcnow() -> datetime:
        return datetime.now(timezone.utc)
