"""
Client IP helpers.

In cloud deployments the app is typically behind a reverse proxy / load balancer.
If we blindly trust `X-Forwarded-For` we open ourselves to spoofing, so this
parsing is gated behind a Settings flag.
"""

from __future__ import annotations

from fastapi import Request

from app.config import settings


def get_client_ip(request: Request) -> str:
    """
    Resolve the best-effort client IP.

    - Default: use Starlette's `request.client.host`
    - If TRUST_PROXY_HEADERS=true: use the left-most X-Forwarded-For value
    """

    if getattr(settings, "TRUST_PROXY_HEADERS", False):
        xff = request.headers.get("x-forwarded-for")
        if xff:
            # "client, proxy1, proxy2" -> take first hop
            ip = xff.split(",")[0].strip()
            if ip:
                return ip

    client = request.client
    if client and client.host:
        return client.host
    return "unknown"

