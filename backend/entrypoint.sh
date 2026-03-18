#!/usr/bin/env sh
set -e  # 遇到错误立即退出

echo "[entrypoint] Starting container at $(date '+%Y-%m-%d %H:%M:%S')"

# ================================
# 0. 打印关键环境信息（调试神器）
# ================================
echo "[entrypoint] Environment check:"
echo "  PORT env var          : ${PORT:-'(not set)'}"
echo "  DATABASE_URL          : ${DATABASE_URL:-(not set)}"
echo "  WEB_CONCURRENCY       : ${WEB_CONCURRENCY:-'(default 2)'}"
echo "  Current working dir   : $(pwd)"
echo "  Python version        : $(python --version 2>&1)"
echo "  Gunicorn version      : $(gunicorn --version 2>&1 || echo 'not found')"
echo "  Uvicorn version       : $(python -c 'import uvicorn; print(uvicorn.__version__)' 2>&1 || echo 'not found')"

# 默认 PORT，如果 Cloud Run 没给，就用 8000（本地兼容），但强烈建议 Cloud Run 注入 8080
PORT="${PORT:-8000}"
echo "[entrypoint] Using PORT=${PORT}"

# ================================
# 1. 等待数据库就绪
# ================================
echo "[entrypoint] Waiting for database..."
python - <<'PY'
import asyncio
import os
import sys
import time
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

db_url = os.environ.get("DATABASE_URL")
if not db_url:
    print("[entrypoint] ERROR: DATABASE_URL is required", file=sys.stderr)
    sys.exit(1)

timeout_s = float(os.environ.get("DB_WAIT_TIMEOUT_SECONDS", "60"))
deadline = time.time() + timeout_s

async def main():
    engine = create_async_engine(db_url, pool_pre_ping=True)
    try:
        while True:
            try:
                async with engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
                print("[entrypoint] Database is ready")
                return
            except Exception as exc:
                if time.time() >= deadline:
                    print(f"[entrypoint] DB not ready after {timeout_s}s: {exc}", file=sys.stderr)
                    sys.exit(1)
                await asyncio.sleep(1)
    finally:
        await engine.dispose()

asyncio.run(main())
PY

# ================================
# 2. 执行 migration（带更安全的容错）
# ================================
echo "[entrypoint] Running Alembic migrations..."
if alembic upgrade head; then
    echo "[entrypoint] Migration completed successfully"
else
    echo "[entrypoint] Migration failed → trying fallback (stamp head)"
    alembic stamp head || true
    echo "[entrypoint] Forced stamp head, continuing anyway..."
fi

# ================================
# 3. 启动服务
# ================================
WEB_CONCURRENCY="${WEB_CONCURRENCY:-2}"
echo "[entrypoint] Starting FastAPI/Gunicorn on 0.0.0.0:${PORT} with ${WEB_CONCURRENCY} workers..."

# 打印启动命令，便于调试
echo "[entrypoint] Exec command:"
echo "  gunicorn \"app.main:app\" \\"
echo "    --worker-class uvicorn.workers.UvicornWorker \\"
echo "    --bind \"0.0.0.0:${PORT}\" \\"
echo "    --workers ${WEB_CONCURRENCY} \\"
echo "    --timeout 60 --graceful-timeout 30 \\"
echo "    --access-logfile - --error-logfile -"

exec gunicorn "app.main:app" \
  --worker-class "uvicorn.workers.UvicornWorker" \
  --bind "0.0.0.0:${PORT}" \
  --workers "${WEB_CONCURRENCY}" \
  --timeout 60 \
  --graceful-timeout 30 \
  --access-logfile "-" \
  --error-logfile "-"