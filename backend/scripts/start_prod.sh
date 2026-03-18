#!/usr/bin/env bash
set -euo pipefail

# Production entrypoint for Linux containers/VMs.
# Requirements:
# - install `requirements-prod.txt`
# - set ENV=production and required secrets

PORT="${PORT:-8000}"
WEB_CONCURRENCY="${WEB_CONCURRENCY:-4}"

exec gunicorn "app.main:app" \
  --worker-class "uvicorn.workers.UvicornWorker" \
  --bind "0.0.0.0:${PORT}" \
  --workers "${WEB_CONCURRENCY}" \
  --timeout 60 \
  --graceful-timeout 30 \
  --access-logfile "-" \
  --error-logfile "-"

