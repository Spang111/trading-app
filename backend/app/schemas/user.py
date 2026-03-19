"""
User-related Pydantic schemas.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class UserStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=6, max_length=100, description="Password")
    wallet_address: Optional[str] = Field(
        None,
        max_length=100,
        description="Wallet address",
    )


class UserLogin(BaseModel):
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Username")
    email: Optional[EmailStr] = Field(None, description="Email address")
    wallet_address: Optional[str] = Field(
        None,
        max_length=100,
        description="Wallet address",
    )


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    wallet_address: Optional[str] = None
    role: UserRole
    status: UserStatus
    email_verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RegistrationResponse(BaseModel):
    message: str
    email: EmailStr
    requires_email_verification: bool


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class VerifyEmailRequest(BaseModel):
    token: str = Field(..., min_length=1)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6, max_length=100)


class MessageResponse(BaseModel):
    message: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
