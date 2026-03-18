"""
安全中间件
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.webhook_security import verify_webhook_ip
from app.config import settings
import time


class SecurityMiddleware(BaseHTTPMiddleware):
    """安全中间件"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # 记录请求开始时间
        start_time = time.time()
        
        # 添加安全响应头
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # 记录请求日志
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
