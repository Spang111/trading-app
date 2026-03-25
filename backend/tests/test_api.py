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
from app.models.payment import Payment, PaymentStatus
from app.models.strategy import Strategy, StrategyStatus
from app.models.strategy import StrategySubscription, SubscriptionStatus
from app.models.user import User, UserRole, UserStatus
from app.services.email_verification_service import EmailVerificationService
from app.services.password_reset_service import PasswordResetService
from app.services.trade_service import _select_derivative_markets
from app.utils.security import (
    create_email_verification_token,
    create_password_reset_token,
    hash_password,
    verify_password,
)


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


@pytest_asyncio.fixture
async def user_token(client, db_session, email_verification_disabled):
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
    token = response.json().get("access_token")
    assert token
    return {"token": token, "user_id": user.id}


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
async def test_forgot_password_sends_email(client, db_session, monkeypatch):
    username = f"user_{uuid4().hex[:8]}"
    email = f"{username}@example.com"

    user = User(
        username=username,
        email=email,
        password_hash=hash_password("pass12345"),
        role=UserRole.USER,
        is_admin=False,
        status=UserStatus.ACTIVE,
        email_verified=True,
    )
    db_session.add(user)
    await db_session.flush()

    sent = {"count": 0}

    async def fake_send_password_reset_email(self, *, user, request=None):
        sent["count"] += 1
        return "fake-reset-token"

    monkeypatch.setattr(
        PasswordResetService,
        "send_password_reset_email",
        fake_send_password_reset_email,
    )

    response = await client.post("/api/auth/forgot-password", json={"email": email})
    assert response.status_code == 200
    assert response.json()["message"] == (
        "If that email address exists, a password reset link will arrive shortly."
    )
    assert sent["count"] == 1


@pytest.mark.asyncio
async def test_reset_password(client, db_session):
    username = f"user_{uuid4().hex[:8]}"
    email = f"{username}@example.com"
    old_password = "pass12345"
    new_password = "newpass123"

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(old_password),
        role=UserRole.USER,
        is_admin=False,
        status=UserStatus.ACTIVE,
        email_verified=True,
    )
    db_session.add(user)
    await db_session.flush()

    token = create_password_reset_token(
        user_id=user.id,
        email=user.email,
        password_hash=user.password_hash,
    )

    response = await client.post(
        "/api/auth/reset-password",
        json={"token": token, "new_password": new_password},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Password reset successful. You can log in now."

    await db_session.refresh(user)
    assert verify_password(new_password, user.password_hash)


def test_select_derivative_markets_filters_symbols():
    class FakeExchange:
        markets = {
            "BTC/USDT:USDT": {
                "symbol": "BTC/USDT:USDT",
                "swap": True,
                "active": True,
                "id": "BTCUSDT",
            },
            "ETH/USDT:USDT": {
                "symbol": "ETH/USDT:USDT",
                "future": True,
                "active": True,
                "id": "ETHUSDT",
            },
            "BTC/USDT": {
                "symbol": "BTC/USDT",
                "spot": True,
                "active": True,
                "id": "BTCUSDT_SPOT",
            },
            "DOGE/USDT:USDT": {
                "symbol": "DOGE/USDT:USDT",
                "swap": True,
                "active": False,
                "id": "DOGEUSDT",
            },
        }

    selected = _select_derivative_markets(
        FakeExchange(),
        symbol_filter={"BTC/USDT:USDT", "DOGE/USDT:USDT"},
    )

    assert list(selected.keys()) == ["BTC/USDT:USDT"]


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


@pytest.mark.asyncio
async def test_public_strategy_list_excludes_inactive(client, db_session):
    active_strategy = Strategy(
        name="Active Strategy",
        description="shown",
        apy="12.5",
        max_drawdown="15",
        win_rate="55",
        monthly_price="19.99",
        yearly_price="199.99",
        tag="live",
        status=StrategyStatus.ACTIVE,
    )
    inactive_strategy = Strategy(
        name="Inactive Strategy",
        description="hidden",
        apy="10",
        max_drawdown="12",
        win_rate="50",
        monthly_price="9.99",
        yearly_price="99.99",
        tag="archived",
        status=StrategyStatus.INACTIVE,
    )
    db_session.add_all([active_strategy, inactive_strategy])
    await db_session.flush()

    response = await client.get("/api/strategies")
    assert response.status_code == 200

    names = {item["name"] for item in response.json()}
    assert "Active Strategy" in names
    assert "Inactive Strategy" not in names


@pytest.mark.asyncio
async def test_admin_strategy_list_includes_inactive(client, admin_token, db_session):
    active_strategy = Strategy(
        name="Admin Active Strategy",
        description="shown",
        apy="15",
        max_drawdown="11",
        win_rate="57",
        monthly_price="29.99",
        yearly_price="299.99",
        tag="active",
        status=StrategyStatus.ACTIVE,
    )
    inactive_strategy = Strategy(
        name="Admin Inactive Strategy",
        description="shown to admin",
        apy="9",
        max_drawdown="20",
        win_rate="45",
        monthly_price="14.99",
        yearly_price="149.99",
        tag="inactive",
        status=StrategyStatus.INACTIVE,
    )
    db_session.add_all([active_strategy, inactive_strategy])
    await db_session.flush()

    response = await client.get(
        "/api/strategies/admin/list",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200

    names = {item["name"] for item in response.json()}
    assert "Admin Active Strategy" in names
    assert "Admin Inactive Strategy" in names


@pytest.mark.asyncio
async def test_create_payment_creates_pending_subscription(client, admin_token, user_token, db_session):
    strategy_payload = {
        "name": "Payment Flow Strategy",
        "description": "manual review flow",
        "apy": "18.5",
        "max_drawdown": "12",
        "win_rate": "61",
        "monthly_price": "49.99",
        "yearly_price": "499.99",
        "tag": "btc",
    }
    strategy_response = await client.post(
        "/api/strategies",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=strategy_payload,
    )
    assert strategy_response.status_code in (200, 201)
    strategy_id = strategy_response.json()["id"]

    response = await client.post(
        "/api/payments/create",
        headers={"Authorization": f"Bearer {user_token['token']}"},
        json={"strategy_id": strategy_id, "plan_type": "monthly"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert data["payment_method"] == "manual_wallet"
    assert "payment_note" in data

    payment = await db_session.get(Payment, data["id"])
    assert payment is not None
    assert payment.status == PaymentStatus.PENDING
    assert payment.subscription_id is not None

    subscription = await db_session.get(StrategySubscription, payment.subscription_id)
    assert subscription is not None
    assert subscription.user_id == user_token["user_id"]
    assert subscription.status == SubscriptionStatus.PENDING


@pytest.mark.asyncio
async def test_admin_approve_payment_activates_subscription(client, admin_token, user_token, db_session):
    strategy_payload = {
        "name": "Approval Flow Strategy",
        "description": "approve pending order",
        "apy": "15.0",
        "max_drawdown": "10",
        "win_rate": "58",
        "monthly_price": "29.99",
        "yearly_price": "299.99",
        "tag": "eth",
    }
    strategy_response = await client.post(
        "/api/strategies",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=strategy_payload,
    )
    assert strategy_response.status_code in (200, 201)
    strategy_id = strategy_response.json()["id"]

    create_payment_response = await client.post(
        "/api/payments/create",
        headers={"Authorization": f"Bearer {user_token['token']}"},
        json={"strategy_id": strategy_id, "plan_type": "monthly"},
    )
    assert create_payment_response.status_code == 200
    payment_id = create_payment_response.json()["id"]

    submit_tx_hash_response = await client.post(
        f"/api/payments/verify?payment_id={payment_id}",
        headers={"Authorization": f"Bearer {user_token['token']}"},
        json={"tx_hash": f"tx_{uuid4().hex}{uuid4().hex}"},
    )
    assert submit_tx_hash_response.status_code == 200

    approve_response = await client.post(
        f"/api/payments/admin/{payment_id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert approve_response.status_code == 200

    payment = await db_session.get(Payment, payment_id)
    assert payment is not None
    assert payment.status == PaymentStatus.SUCCESS
    assert payment.verified_by is not None
    assert payment.subscription_id is not None

    subscription = await db_session.get(StrategySubscription, payment.subscription_id)
    assert subscription is not None
    assert subscription.status == SubscriptionStatus.ACTIVE
