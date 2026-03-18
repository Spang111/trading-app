"""
Create an initial admin user.

Usage (from backend/):
  python scripts/create_admin.py --username admin --email admin@example.com

The password is read from --password / ADMIN_PASSWORD or prompted securely.
"""

from __future__ import annotations

import argparse
import asyncio
import os
from getpass import getpass

from sqlalchemy import or_, select

from app.database import async_session_maker
from app.models.user import User, UserRole, UserStatus
from app.utils.security import hash_password


async def create_admin_user(*, username: str, email: str, password: str) -> User:
    async with async_session_maker() as session:
        existing = await session.execute(
            select(User).where(or_(User.username == username, User.email == email))
        )
        if existing.scalar_one_or_none() is not None:
            raise SystemExit("User already exists (username or email).")

        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
            is_admin=True,
            status=UserStatus.ACTIVE,
        )
        session.add(user)
        await session.flush()
        await session.refresh(user)
        await session.commit()
        return user


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create an initial admin user.")
    parser.add_argument(
        "--username",
        default=os.getenv("ADMIN_USERNAME"),
        help="Admin username (or ADMIN_USERNAME).",
    )
    parser.add_argument(
        "--email",
        default=os.getenv("ADMIN_EMAIL"),
        help="Admin email (or ADMIN_EMAIL).",
    )
    parser.add_argument(
        "--password",
        default=os.getenv("ADMIN_PASSWORD"),
        help="Admin password (or ADMIN_PASSWORD). If omitted, you'll be prompted.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.username:
        raise SystemExit("--username (or ADMIN_USERNAME) is required.")
    if not args.email:
        raise SystemExit("--email (or ADMIN_EMAIL) is required.")

    password = args.password or getpass("Admin password: ")
    if not password:
        raise SystemExit("Password is required.")

    user = asyncio.run(
        create_admin_user(username=args.username, email=args.email, password=password)
    )
    print(f"Created admin user: username={user.username} id={user.id}")


if __name__ == "__main__":
    main()

