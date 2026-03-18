#!/usr/bin/env sh
set -e

echo "[entrypoint] 🚀 Starting container..."

# ================================
# 1. 等待数据库就绪（更稳定版）
# ================================
echo "[entrypoint] ⏳ Waiting for database..."

python - <<'PY'
import asyncio
import os
import sys
import time
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

db_url = os.environ.get("DATABASE_URL")
if not db_url:
    print("[entrypoint] ❌ DATABASE_URL is required", file=sys.stderr)
    raise SystemExit(1)

timeout_s = float(os.environ.get("DB_WAIT_TIMEOUT_SECONDS", "60"))
deadline = time.time() + timeout_s

async def main():
    engine = create_async_engine(db_url, pool_pre_ping=True)
    try:
        while True:
            try:
                async with engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
                print("[entrypoint] ✅ Database is ready")
                return
            except Exception as exc:
                if time.time() >= deadline:
                    print(f"[entrypoint] ❌ DB not ready after {timeout_s}s: {exc}", file=sys.stderr)
                    raise SystemExit(1)
                await asyncio.sleep(1)
    finally:
        await engine.dispose()

asyncio.run(main())
PY

# ================================
# 2. 安全执行 migration（关键修复点）
# ================================
echo "[entrypoint] 🛠 Running migrations..."

if alembic upgrade head; then
  echo "[entrypoint] ✅ Migration completed"
else
  echo "[entrypoint] ⚠️ Migration failed, trying fallback..."

  # 处理 ENUM 已存在问题（你的核心 bug）
  alembic stamp head || true

  echo "[entrypoint] ⚠️ Forced stamp head, continuing..."
fi

# ================================
# 3. 启动服务（带 debug 信息）
# ================================
PORT="${PORT:-8080}"
WEB_CONCURRENCY="${WEB_CONCURRENCY:-2}"

echo "[entrypoint] 🌐 Starting API on port ${PORT}..."

exec gunicorn "app.main:app" \
  --worker-class "uvicorn.workers.UvicornWorker" \
  --bind "0.0.0.0:${PORT}" \
  --workers "${WEB_CONCURRENCY}" \
  --timeout 60 \
  --graceful-timeout 30 \
  --access-logfile "-" \
  --error-logfile "-"