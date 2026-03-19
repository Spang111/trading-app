"""
FastAPI application entrypoint.
"""
from contextlib import asynccontextmanager
import asyncio
import logging
from urllib.parse import urlparse

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import engine, init_db
from app.middleware.rate_limit_middleware import RateLimitMiddleware
from app.middleware.security_middleware import SecurityMiddleware
from app.routers import api_router
from app.services.trade_service import warmup_exchange_markets
from app.utils.task_manager import TaskManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize tables in development only.
    if settings.DEBUG:
        await init_db()

    # Warm up exchange markets cache in the background so Cloud Run can
    # serve health checks quickly during cold starts.
    exchange_ids = settings.exchange_cache_list
    task_manager: TaskManager | None = getattr(app.state, "task_manager", None)
    if exchange_ids and task_manager is not None:
        task_manager.create_task(
            warmup_exchange_markets(exchange_ids),
            name="exchange-market-warmup",
        )
    elif exchange_ids:
        await warmup_exchange_markets(exchange_ids)

    yield

    # Graceful shutdown: stop background tasks then dispose DB connections.
    task_manager = getattr(app.state, "task_manager", None)
    if task_manager is not None:
        await task_manager.shutdown(
            timeout_seconds=float(settings.BACKGROUND_TASK_SHUTDOWN_TIMEOUT_SECONDS or 10.0)
        )
    await engine.dispose()


def _configure_logging() -> None:
    level_name = (settings.LOG_LEVEL or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def create_app() -> FastAPI:
    _configure_logging()

    docs_url = None if settings.ENV == "production" else "/docs"
    redoc_url = None if settings.ENV == "production" else "/redoc"
    openapi_url = None if settings.ENV == "production" else "/openapi.json"

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="QuantFlow Backend API",
        lifespan=lifespan,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
    )

    app.state.task_manager = TaskManager()

    cors_origins = settings.cors_origin_list
    if settings.ENV == "production" and not cors_origins:
        raise RuntimeError("BACKEND_CORS_ORIGINS is required when ENV=production.")
    if settings.ENV != "production" and not cors_origins:
        cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(SecurityMiddleware)
    if settings.RATE_LIMIT_ENABLED:
        app.add_middleware(RateLimitMiddleware, requests_per_second=int(settings.RATE_LIMIT_RPS or 10))

    app.include_router(api_router, prefix="/api")

    @app.get("/live")
    async def liveness_check():
        return {"status": "alive", "version": settings.APP_VERSION}

    @app.get("/health")
    async def health_check():
        # Readiness: verify critical dependencies.
        details: dict = {"version": settings.APP_VERSION, "db": "ok", "proxy": "skipped"}

        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception as exc:
            details["db"] = f"error: {exc.__class__.__name__}"
            return JSONResponse(status_code=503, content={"status": "unhealthy", **details})

        proxy_url = (settings.PROXY_URL or "").strip()
        if proxy_url and settings.ENV == "production":
            details["proxy"] = "ok"
            try:
                parsed = urlparse(proxy_url)
                host = parsed.hostname
                port = parsed.port
                if not host:
                    raise ValueError("invalid PROXY_URL hostname")
                if port is None:
                    scheme = (parsed.scheme or "http").lower()
                    port = 1080 if scheme.startswith("socks") else (443 if scheme == "https" else 80)

                timeout = float(settings.HEALTHCHECK_TIMEOUT_SECONDS or 1.0)
                reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
                writer.close()
                try:
                    await writer.wait_closed()
                except Exception:
                    pass
                _ = reader
            except Exception as exc:
                details["proxy"] = f"error: {exc.__class__.__name__}"
                return JSONResponse(status_code=503, content={"status": "unhealthy", **details})

        return {"status": "healthy", **details}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    if settings.ENV == "production":
        raise RuntimeError(
            "Do not run uvicorn.run() in production. Use Gunicorn + Uvicorn workers instead."
        )

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
