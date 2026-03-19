"""
Application settings (Pydantic v2).

Goals:
- No hard-coded secrets in code.
- Production fails fast on missing critical env vars.
- CORS origins configurable via JSON list or comma-separated string.
"""

from __future__ import annotations

import json
import logging
from typing import Annotated, List, Literal, Optional, Sequence

from pydantic import AliasChoices, AnyHttpUrl, Field, Json, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_list_from_env(value: object) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return []
        if raw.startswith("["):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except json.JSONDecodeError:
                pass
        return [item.strip() for item in raw.split(",") if item.strip()]
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    raise TypeError("Expected a list, JSON string, or comma-separated string.")


class Settings(BaseSettings):
    # Environment
    ENV: Literal["development", "test", "production"] = "development"

    # App
    APP_NAME: str = "QuantFlow API"
    APP_VERSION: str = "1.0.0"
    BACKEND_PUBLIC_URL: Optional[AnyHttpUrl] = None
    FRONTEND_APP_URL: Optional[AnyHttpUrl] = None

    # Debug / logging
    DEBUG: Optional[bool] = None
    LOG_LEVEL: Optional[str] = None

    # Proxy / client IP (cloud)
    # Only enable this when the app is behind a trusted reverse proxy / LB that
    # sets X-Forwarded-For. Otherwise clients can spoof their IP.
    TRUST_PROXY_HEADERS: bool = False

    # JWT (required)
    SECRET_KEY: str = Field(min_length=1)
    EMAIL_TOKEN_SECRET: Optional[str] = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database (required)
    DATABASE_URL: str = Field(min_length=1)

    # TradingView webhook security (passphrase required)
    TRADINGVIEW_IP_WHITELIST: str = "52.89.214.238,34.212.75.30,54.218.48.199"
    TRADINGVIEW_PASSPHRASE: str = Field(min_length=1)

    # Exchanges
    DEFAULT_EXCHANGE: str = "okx"
    EXCHANGE_MARKETS_CACHE: str = "okx,binance"
    PROXY_URL: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("PROXY_URL", "HTTP_PROXY"),
    )
    MONITOR_SYMBOLS: List[str] = [
        "BTC/USDT:USDT",
        "ETH/USDT:USDT",
        "SOL/USDT:USDT",
        "BNB/USDT:USDT",
        "BONK/USDT:USDT",
        "OKB/USDT:USDT",
        "UNI/USDT:USDT",
        "DOGE/USDT:USDT",
        "HYPE/USDT:USDT",
        "VIRTUAL/USDT:USDT",
    ]

    # NowPayments (optional; manual payments can work without it)
    NOWPAYMENTS_API_KEY: Optional[str] = None
    NOWPAYMENTS_API_URL: str = "https://api.nowpayments.io/v1"

    # Encryption key for API credentials (optional; kept for future use)
    ENCRYPTION_KEY: Optional[str] = None

    # Email verification / SMTP
    EMAIL_VERIFICATION_REQUIRED: bool = False
    EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS: int = 60
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    SMTP_FROM_NAME: Optional[str] = None
    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False

    # CORS: supports env var as JSON list or comma-separated string.
    BACKEND_CORS_ORIGINS: Annotated[List[AnyHttpUrl], Json()] = Field(
        # Use JSON string as the *raw* default so pydantic-settings won't force JSON parsing
        # (we support both JSON and comma-separated strings via the validator below).
        default='["http://localhost:3000","http://127.0.0.1:3000"]',
        validation_alias=AliasChoices("BACKEND_CORS_ORIGINS", "CORS_ORIGINS"),
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _validate_backend_cors_origins(cls, value: object) -> str:
        # This field is annotated with Json(), so we must return a JSON string here.
        # Accept:
        # - JSON list string: ["https://a.com","https://b.com"]
        # - CSV string: https://a.com,https://b.com
        # - python list/tuple/set of strings
        items = _parse_list_from_env(value)
        return json.dumps(items)

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def _normalize_log_level(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned.upper() if cleaned else None
        return value

    @model_validator(mode="after")
    def _apply_defaults_and_validate_production(self) -> "Settings":
        if self.DEBUG is None:
            self.DEBUG = self.ENV != "production"

        if self.LOG_LEVEL is None:
            self.LOG_LEVEL = "DEBUG" if self.DEBUG else "INFO"

        if self.SMTP_USE_TLS and self.SMTP_USE_SSL:
            raise ValueError("SMTP_USE_TLS and SMTP_USE_SSL cannot both be True.")

        if self.EMAIL_VERIFICATION_REQUIRED:
            if not self.SMTP_HOST:
                raise ValueError("SMTP_HOST is required when EMAIL_VERIFICATION_REQUIRED=True.")
            if not self.SMTP_FROM_EMAIL:
                raise ValueError(
                    "SMTP_FROM_EMAIL is required when EMAIL_VERIFICATION_REQUIRED=True."
                )

        if self.ENV == "production":
            if self.DEBUG:
                raise ValueError("DEBUG must be False when ENV=production.")
            if self.LOG_LEVEL == "DEBUG":
                raise ValueError("LOG_LEVEL must not be DEBUG when ENV=production.")

            # CORS should be explicitly configured for production and must not allow localhost.
            if not self.BACKEND_CORS_ORIGINS:
                raise ValueError("BACKEND_CORS_ORIGINS is required when ENV=production.")

            disallowed_hosts = {"localhost", "127.0.0.1", "0.0.0.0"}
            for origin in self.BACKEND_CORS_ORIGINS:
                if origin.host in disallowed_hosts:
                    raise ValueError(
                        "BACKEND_CORS_ORIGINS must not include localhost/127.0.0.1 in production."
                    )
                # Origins must not contain path/query/fragment.
                if getattr(origin, "path", "/") not in ("", "/"):
                    raise ValueError("BACKEND_CORS_ORIGINS must not include a URL path.")

        return self

    @property
    def tradingview_ips(self) -> List[str]:
        return [ip.strip() for ip in self.TRADINGVIEW_IP_WHITELIST.split(",") if ip.strip()]

    @property
    def exchange_cache_list(self) -> List[str]:
        return [ex.strip() for ex in self.EXCHANGE_MARKETS_CACHE.split(",") if ex.strip()]

    @property
    def cors_origin_list(self) -> List[str]:
        # Backward-compatible helper for CORSMiddleware (no trailing slash).
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS]

    @property
    def email_token_secret(self) -> str:
        return (self.EMAIL_TOKEN_SECRET or self.SECRET_KEY).strip()

    @property
    def smtp_from_name(self) -> str:
        return (self.SMTP_FROM_NAME or self.APP_NAME).strip()

    # Rate limiting (in-memory; for multi-instance deployments use Redis-based limiting)
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_RPS: int = 10

    # Health / shutdown
    HEALTHCHECK_TIMEOUT_SECONDS: float = 1.0
    BACKGROUND_TASK_SHUTDOWN_TIMEOUT_SECONDS: float = 10.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
