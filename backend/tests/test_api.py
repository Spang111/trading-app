import os
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("EXCHANGE_MARKETS_CACHE", "")
os.environ.setdefault("ENV", "test")
os.environ.setdefault("TRADINGVIEW_PASSPHRASE", "test_passphrase")
os.environ.setdefault("BACKEND_CORS_ORIGINS", "http://localhost:3000")

from app.database import async_session_maker, get_db
from app.main import create_app
from app.models.strategy import Strategy
from app.models.user import User, UserRole, UserStatus
from app.utils.security import hash_password


import asyncio


@pytest.fixture(scope="session")
def event_loop():
    """强制整个测试会话共用同一个事件循环，防止数据库连接池因循环关闭而报错"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


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
async def admin_token(client, db_session):
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
    )
    db_session.add(admin)
    await db_session.flush()

    r = await client.post(
        "/api/auth/login",
        data={"username": username, "password": password},
    )
    assert r.status_code == 200
    token = r.json().get("access_token")
    assert token
    return token


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "healthy"


@pytest.mark.asyncio
async def test_login(client, db_session):
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
    )
    db_session.add(user)
    await db_session.flush()

    r = await client.post(
        "/api/auth/login",
        data={"username": username, "password": password},
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("access_token")


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
    r = await client.post(
        "/api/strategies",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=payload,
    )
    assert r.status_code in (200, 201)
    data = r.json()
    strategy_id = data.get("id")
    assert strategy_id

    strategy = await db_session.get(Strategy, strategy_id)
    assert strategy is not None
    assert strategy.name == payload["name"]
