"""
Simple in-memory rate limiting middleware.

Notes for production:
- This limiter is per-process. If you run multiple workers/instances, limits are not shared.
- For multi-instance deployments, prefer a shared-store limiter (Redis) such as SlowAPI.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.utils.ip import get_client_ip


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        requests_per_second: int = 10,
        *,
        window_seconds: float = 1.0,
        cleanup_interval_seconds: float = 60.0,
        stale_client_seconds: float = 10 * 60.0,
        max_clients: int = 50_000,
    ) -> None:
        super().__init__(app)
        self.requests_per_second = max(1, int(requests_per_second))
        self.window_seconds = float(window_seconds)
        self.cleanup_interval_seconds = float(cleanup_interval_seconds)
        self.stale_client_seconds = float(stale_client_seconds)
        self.max_clients = int(max_clients)

        self.request_history: Dict[str, Deque[float]] = defaultdict(deque)
        self.last_seen: Dict[str, float] = {}
        self._last_cleanup_at = time.monotonic()

    async def dispatch(self, request: Request, call_next) -> Response:
        # Avoid limiting health probes and other infra calls.
        if request.url.path in ("/health", "/live"):
            return await call_next(request)

        client_ip = get_client_ip(request)
        now = time.monotonic()

        # Periodic cleanup to avoid unbounded memory growth.
        if (
            (now - self._last_cleanup_at) >= self.cleanup_interval_seconds
            or len(self.last_seen) > self.max_clients
        ):
            cutoff = now - self.stale_client_seconds
            stale_keys = [ip for ip, ts in self.last_seen.items() if ts < cutoff]
            for ip in stale_keys:
                self.last_seen.pop(ip, None)
                self.request_history.pop(ip, None)
            self._last_cleanup_at = now

        self.last_seen[client_ip] = now

        dq = self.request_history[client_ip]
        window_start = now - self.window_seconds
        while dq and dq[0] < window_start:
            dq.popleft()

        if len(dq) >= self.requests_per_second:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests"},
            )

        dq.append(now)
        return await call_next(request)

