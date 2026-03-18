#!/usr/bin/env python3
"""
Pre-flight environment checks for cloud deployment.

Run this before `docker compose up` to catch common misconfigurations early:
- DATABASE_URL format validation (postgresql+asyncpg)
- SECRET_KEY strength sanity checks
- BACKEND_CORS_ORIGINS must include at least one non-localhost "real" domain
"""

from __future__ import annotations

import json
import os
import re
import sys
from ipaddress import ip_address
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import unquote, urlparse


def _die(message: str, *, code: int = 1) -> "None":
    print(message, file=sys.stderr)
    raise SystemExit(code)


def _parse_env_file(path: Path) -> Dict[str, str]:
    if not path.exists():
        _die(f"ERROR: env file not found: {path}")

    env: Dict[str, str] = {}
    for idx, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("export "):
            line = line[len("export ") :].lstrip()

        if "=" not in line:
            _die(f"ERROR: invalid line (missing '=') at {path}:{idx}: {raw_line!r}")

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if not key:
            _die(f"ERROR: invalid line (empty key) at {path}:{idx}: {raw_line!r}")

        # Strip optional surrounding quotes
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]

        env[key] = value

    return env


def _parse_list(value: str) -> List[str]:
    raw = (value or "").strip()
    if not raw:
        return []

    if raw.startswith("["):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return [item.strip() for item in raw.split(",") if item.strip()]
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
        return []

    return [item.strip() for item in raw.split(",") if item.strip()]


def _is_ip(host: str) -> bool:
    try:
        ip_address(host)
        return True
    except ValueError:
        return False


def _validate_database_url(env: Dict[str, str]) -> List[str]:
    errors: List[str] = []
    url = env.get("DATABASE_URL", "").strip()
    if not url:
        return ["DATABASE_URL is missing or empty"]

    if "postgresql+asyncpg://postgresql://" in url:
        errors.append("DATABASE_URL has a nested scheme (postgresql+asyncpg://postgresql://...). Fix it.")
        return errors

    parsed = urlparse(url)
    if parsed.scheme != "postgresql+asyncpg":
        errors.append("DATABASE_URL must start with postgresql+asyncpg://")
        return errors

    if not parsed.hostname:
        errors.append("DATABASE_URL is missing hostname")
    if not parsed.username:
        errors.append("DATABASE_URL is missing username")
    if parsed.password is None or parsed.password == "":
        errors.append("DATABASE_URL is missing password")
    dbname = (parsed.path or "").lstrip("/")
    if not dbname:
        errors.append("DATABASE_URL is missing database name (path)")

    # Optional: ensure Compose's POSTGRES_* variables match DATABASE_URL
    pg_user = env.get("POSTGRES_USER")
    pg_password = env.get("POSTGRES_PASSWORD")
    pg_db = env.get("POSTGRES_DB")

    if pg_user and parsed.username and parsed.username != pg_user:
        errors.append("POSTGRES_USER does not match DATABASE_URL username")
    if pg_password and parsed.password is not None:
        # urlparse returns the percent-decoded password? No, it returns raw; decode for comparison.
        if unquote(parsed.password) != pg_password:
            errors.append("POSTGRES_PASSWORD does not match DATABASE_URL password")
    if pg_db and dbname and dbname != pg_db:
        errors.append("POSTGRES_DB does not match DATABASE_URL database name")

    return errors


def _validate_secret_key(env: Dict[str, str]) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    key = env.get("SECRET_KEY", "")
    if not key:
        return ["SECRET_KEY is missing or empty"], []

    if len(key) < 32:
        errors.append("SECRET_KEY is too short (must be >= 32 characters).")

    lowered = key.strip().lower()
    banned_substrings = [
        "change_me",
        "your-secret",
        "secret_key",
        "secretkey",
        "password",
        "quantflow",
    ]
    if any(s in lowered for s in banned_substrings):
        errors.append("SECRET_KEY looks like a placeholder. Replace it with a long random secret.")

    if any(ch.isspace() for ch in key):
        warnings.append("SECRET_KEY contains whitespace. This is allowed but easy to break when copying.")

    # Simple complexity hint (not a strict requirement for random URL-safe tokens)
    classes = 0
    classes += 1 if re.search(r"[a-z]", key) else 0
    classes += 1 if re.search(r"[A-Z]", key) else 0
    classes += 1 if re.search(r"[0-9]", key) else 0
    classes += 1 if re.search(r"[^a-zA-Z0-9]", key) else 0
    if classes < 3:
        warnings.append("SECRET_KEY has low character variety. Consider using a longer random token.")

    return errors, warnings


def _validate_cors_origins(env: Dict[str, str]) -> List[str]:
    errors: List[str] = []
    raw = env.get("BACKEND_CORS_ORIGINS", "").strip()
    if not raw:
        return ["BACKEND_CORS_ORIGINS is missing or empty"]

    origins = _parse_list(raw)
    if not origins:
        return ["BACKEND_CORS_ORIGINS could not be parsed (expected JSON list or comma-separated URLs)"]

    disallowed_hosts = {"localhost", "127.0.0.1", "0.0.0.0"}
    has_real_domain = False

    for origin in origins:
        if origin == "*":
            errors.append("BACKEND_CORS_ORIGINS must not be '*' in production.")
            continue

        p = urlparse(origin)
        if p.scheme not in ("http", "https"):
            errors.append(f"CORS origin must be http/https: {origin!r}")
            continue
        if not p.hostname:
            errors.append(f"CORS origin missing hostname: {origin!r}")
            continue
        if p.hostname in disallowed_hosts:
            errors.append(f"CORS origin must not use localhost in production: {origin!r}")
            continue
        if (p.path or "/") not in ("", "/") or p.params or p.query or p.fragment:
            errors.append(f"CORS origin must not include path/query/fragment: {origin!r}")
            continue

        if not _is_ip(p.hostname) and "." in p.hostname:
            has_real_domain = True

    if not has_real_domain:
        errors.append("BACKEND_CORS_ORIGINS must include at least one non-localhost domain (e.g. https://app.example.com).")

    return errors


def _validate_prod_flags(env: Dict[str, str]) -> List[str]:
    errors: List[str] = []

    if env.get("ENV") != "production":
        errors.append("ENV must be set to 'production'.")
    if env.get("DEBUG", "").strip().lower() not in ("false", "0", "no"):
        errors.append("DEBUG must be False in production (set DEBUG=False).")
    if env.get("LOG_LEVEL", "").strip().upper() == "DEBUG":
        errors.append("LOG_LEVEL must not be DEBUG in production (use INFO/WARNING).")

    return errors


def main(argv: List[str]) -> int:
    env_path = Path(__file__).with_name(".env.production")
    if len(argv) >= 2:
        env_path = Path(argv[1]).expanduser().resolve()

    env = _parse_env_file(env_path)

    errors: List[str] = []
    warnings: List[str] = []

    errors.extend(_validate_prod_flags(env))
    errors.extend(_validate_database_url(env))
    cors_errors = _validate_cors_origins(env)
    errors.extend(cors_errors)
    sk_errors, sk_warnings = _validate_secret_key(env)
    errors.extend(sk_errors)
    warnings.extend(sk_warnings)

    if errors:
        print("ENV CHECK FAILED:\n", file=sys.stderr)
        for e in errors:
            print(f"- {e}", file=sys.stderr)
        print("\nFix the issues above, then re-run:\n  python3 check_env.py", file=sys.stderr)
        return 1

    print("ENV CHECK PASSED")
    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"- {w}")

    print("\nTip: generate a strong SECRET_KEY with:")
    print('  python3 -c "import secrets; print(secrets.token_urlsafe(64))"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

