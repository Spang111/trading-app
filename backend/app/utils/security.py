"""
Security helpers for passwords, JWTs, and API key encryption.
"""

import base64
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from cryptography.fernet import Fernet
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings


ACCESS_TOKEN_PURPOSE = "access"
EMAIL_VERIFICATION_PURPOSE = "verify_email"


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

secret_key_bytes = base64.urlsafe_b64encode(
    hashlib.sha256(settings.SECRET_KEY.encode()).digest()
)
fernet = Fernet(secret_key_bytes)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _build_expiry(expires_delta: Optional[timedelta], fallback_minutes: int) -> datetime:
    if expires_delta is not None:
        return datetime.now(timezone.utc) + expires_delta
    return datetime.now(timezone.utc) + timedelta(minutes=fallback_minutes)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    to_encode.update(
        {
            "exp": _build_expiry(expires_delta, settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            "purpose": ACCESS_TOKEN_PURPOSE,
        }
    )
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None

    if payload.get("purpose") not in (None, ACCESS_TOKEN_PURPOSE):
        return None

    return payload


def create_email_verification_token(
    *,
    user_id: int,
    email: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    payload = {
        "sub": email,
        "user_id": user_id,
        "purpose": EMAIL_VERIFICATION_PURPOSE,
        "exp": _build_expiry(
            expires_delta,
            settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES,
        ),
    }
    return jwt.encode(payload, settings.email_token_secret, algorithm=settings.ALGORITHM)


def decode_email_verification_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token,
            settings.email_token_secret,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError:
        return None

    if payload.get("purpose") != EMAIL_VERIFICATION_PURPOSE:
        return None

    return payload


def encrypt_api_key(api_key: str) -> str:
    return fernet.encrypt(api_key.encode()).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    return fernet.decrypt(encrypted_key.encode()).decode()
