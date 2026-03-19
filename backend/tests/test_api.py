import asyncio
import os
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

os.environ.setdefault("EXCHANGE_MARKETS_CACHE", "")
os.environ.setdefault("ENV", "test")
os.environ.setdefault("TRADINGVIEW_PASSPHRASE", "test_passphrase")
os.environ.setdefault("BACKEND_CORS_ORIGINS", "http://localhost:3000")
os.environ.setdefault("EMAIL_VERIFICATION_REQUIRED", "false")

from app.config import settings
from app.database import async_session_maker, get_db
from app.main import create_app
from app.models.strategy import Strategy
from app.models.user import User, UserRole, UserStatus
from app.services.email_verification_service import EmailVerificationService
from app.utils.security import create_email_verification_token, hash_password


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def email_verification_disabled():
    original = settings.EMAIL_VERIFICATION_REQUIRED
    settings.EMAIL_VERIFICATION_REQUIRED = False
    try:
        yield
    finally:
        settings.EMAIL_VERIFICATION_REQUIRED = original


@pytest.fixture
def email_verification_enabled():
    original = settings.EMAIL_VERIFICATION_REQUIRED
    settings.EMAIL_VERIFICATION_REQUIRED = True
    try:
        yield
    finally:
        settings.EMAIL_VERIFICATION_REQUIRED = original


@pytest_asyncio.fixture
async def db_session():
    async with async_session_maker() as session:
        await session.begin()
        try:
            yield session
        finally:
            await session.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    app = create_app()

    async def override_get_db():
        try:
            yield db_session
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_token(client, db_session, email_verification_disabled):
    username = f"admin_{uuid4().hex[:8]}"
    email = f"{username}@example.com"
    password = "pass12345"

    admin = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        role=UserRole.ADMIN,
        is_admin=True,
        status=UserStatus.ACTIVE,
        email_verified=True,
    )
    db_session.add(admin)
    await db_session.flush()

    response = await client.post(
        "/api/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200
    token = response.json().get("access_token")
    assert token
    return token


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "healthy"


@pytest.mark.asyncio
async def test_login(client, db_session, email_verification_disabled):
    username = f"user_{uuid4().hex[:8]}"
    email = f"{username}@example.com"
    password = "pass12345"

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        role=UserRole.USER,
        is_admin=False,
        status=UserStatus.ACTIVE,
        email_verified=True,
    )
    db_session.add(user)
    await db_session.flush()

    response = await client.post(
        "/api/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("access_token")


@pytest.mark.asyncio
async def test_login_rejects_unverified_email(client, db_session, email_verification_enabled):
    username = f"user_{uuid4().hex[:8]}"
    email = f"{username}@example.com"
    password = "pass12345"

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        role=UserRole.USER,
        is_admin=False,
        status=UserStatus.ACTIVE,
        email_verified=False,
    )
    db_session.add(user)
    await db_session.flush()

    response = await client.post(
        "/api/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Email address has not been verified."


@pytest.mark.asyncio
async def test_register_requires_email_verification(
    client,
    db_session,
    email_verification_enabled,
    monkeypatch,
):
    sent = {"count": 0}

    async def fake_send_verification_email(self, *, user, request=None):
        sent["count"] += 1
        return "fake-token"

    monkeypatch.setattr(
        EmailVerificationService,
        "send_verification_email",
        fake_send_verification_email,
    )

    payload = {
        "username": f"user_{uuid4().hex[:8]}",
        "email": f"verify_{uuid4().hex[:8]}@example.com",
        "password": "pass12345",
        "wallet_address": "0x123",
    }

    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["requires_email_verification"] is True
    assert sent["count"] == 1

    result = await db_session.execute(select(User).where(User.email == payload["email"]))
    user = result.scalar_one()
    assert user.email_verified is False
    assert user.email_verification_sent_at is not None


@pytest.mark.asyncio
async def test_verify_email(client, db_session, email_verification_enabled):
    username = f"user_{uuid4().hex[:8]}"
    email = f"{username}@example.com"

    user = User(
        username=username,
        email=email,
        password_hash=hash_password("pass12345"),
        role=UserRole.USER,
        is_admin=False,
        status=UserStatus.ACTIVE,
        email_verified=False,
    )
    db_session.add(user)
    await db_session.flush()

    token = create_email_verification_token(user_id=user.id, email=user.email)
    response = await client.post("/api/auth/verify-email", json={"token": token})
    assert response.status_code == 200

    await db_session.refresh(user)
    assert user.email_verified is True
    assert user.email_verified_at is not None


@pytest.mark.asyncio
async def test_create_strategy(client, admin_token, db_session):
    payload = {
        "name": "ETH/USDT Strategy",
        "description": "e2e",
        "apy": "12.5",
        "max_drawdown": "25",
        "win_rate": "55",
        "monthly_price": "29.99",
        "yearly_price": "299.0",
        "tag": "eth",
    }
    response = await client.post(
        "/api/strategies",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=payload,
    )
    assert response.status_code in (200, 201)
    data = response.json()
    strategy_id = data.get("id")
    assert strategy_id

    strategy = await db_session.get(Strategy, strategy_id)
    assert strategy is not None
    assert strategy.name == payload["name"]
