#!/usr/bin/env sh
set -eu

echo "[entrypoint] waiting for database..."
python - <<'PY'
import asyncio
import os
import sys
import time

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

db_url = os.environ.get("DATABASE_URL")
if not db_url:
    print("DATABASE_URL is required", file=sys.stderr)
    raise SystemExit(1)

timeout_s = float(os.environ.get("DB_WAIT_TIMEOUT_SECONDS", "60"))
deadline = time.time() + timeout_s

async def main() -> None:
    engine = create_async_engine(db_url, pool_pre_ping=True)
    try:
        while True:
            try:
                async with engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
                print("[entrypoint] database is ready")
                return
            except Exception as exc:
                if time.time() >= deadline:
                    print(
                        f"[entrypoint] database not ready after {timeout_s}s ({exc.__class__.__name__})",
                        file=sys.stderr,
                    )
                    raise SystemExit(1)
                await asyncio.sleep(1)
    finally:
        await engine.dispose()

asyncio.run(main())
PY

RUN_MIGRATIONS_ON_START="${RUN_MIGRATIONS_ON_START:-}"
if [ -z "${RUN_MIGRATIONS_ON_START}" ]; then
  if [ "${ENV:-development}" = "production" ]; then
    RUN_MIGRATIONS_ON_START="false"
  else
    RUN_MIGRATIONS_ON_START="true"
  fi
fi

if [ "${RUN_MIGRATIONS_ON_START}" = "true" ]; then
  echo "[entrypoint] running alembic migrations..."
  alembic upgrade head
else
  echo "[entrypoint] skipping alembic migrations on startup"
fi

PORT="${PORT:-8000}"
WEB_CONCURRENCY="${WEB_CONCURRENCY:-4}"

echo "[entrypoint] starting gunicorn on 0.0.0.0:${PORT} with ${WEB_CONCURRENCY} workers"
exec gunicorn "app.main:app" \
  --worker-class "uvicorn.workers.UvicornWorker" \
  --bind "0.0.0.0:${PORT}" \
  --workers "${WEB_CONCURRENCY}" \
  --timeout 60 \
  --graceful-timeout 30 \
  --access-logfile "-" \
  --error-logfile "-"
