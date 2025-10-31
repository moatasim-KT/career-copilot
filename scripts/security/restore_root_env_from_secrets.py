#!/usr/bin/env python3
"""
Restore root .env values from files in the secrets/ directory without printing secrets.

- Creates a timestamped backup: .env.backup.YYYYmmdd_HHMMSS
- Updates only known keys if corresponding secret files exist:
  * JWT_SECRET_KEY       <- secrets/jwt_secret.txt
  * OPENAI_API_KEY       <- secrets/openai_api_key.txt
  * GROQ_API_KEY         <- secrets/groq_api_key.txt
- Preserves existing values for other keys and file ordering/comments.
- Replaces only placeholder-ish values (e.g., 'your_*', 'test-*', 'test-*secret*').

Usage:
  python scripts/security/restore_root_env_from_secrets.py
"""
from __future__ import annotations

import os
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT / ".env"
SECRETS_DIR = ROOT / "secrets"

KEY_TO_FILE = {
    # Core auth/AI
    "JWT_SECRET_KEY": SECRETS_DIR / "jwt_secret.txt",
    "OPENAI_API_KEY": SECRETS_DIR / "openai_api_key.txt",
    "GROQ_API_KEY": SECRETS_DIR / "groq_api_key.txt",
    "ANTHROPIC_API_KEY": SECRETS_DIR / "anthropic_api_key.txt",
    "GEMINI_API_KEY": SECRETS_DIR / "gemini_api_key.txt",

    # Database & Cache
    # Prefer direct DATABASE_URL file; if absent, we won't synthesize to avoid wrong config
    "DATABASE_URL": SECRETS_DIR / "database_url.txt",
    "REDIS_URL": SECRETS_DIR / "redis_url.txt",

    # SMTP / Email
    "SMTP_PASSWORD": SECRETS_DIR / "smtp_password.txt",
    "SMTP_USERNAME": SECRETS_DIR / "smtp_username.txt",
    "SENDGRID_API_KEY": SECRETS_DIR / "sendgrid_api_key.txt",
}

PLACEHOLDER_PATTERNS = [
    re.compile(r"^your_[a-z0-9_\-]+$", re.IGNORECASE),
    re.compile(r"^test[-_].*$", re.IGNORECASE),
    re.compile(r"^placeholder.*$", re.IGNORECASE),
    re.compile(r"^chang(e|e_me).*", re.IGNORECASE),
]


def is_placeholder(value: str) -> bool:
    v = value.strip().strip('"\'')
    return any(p.match(v) for p in PLACEHOLDER_PATTERNS)


def load_env_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def parse_env(lines: list[str]) -> list[tuple[str, str]]:
    kv = []
    for line in lines:
        if not line or line.lstrip().startswith("#") or "=" not in line:
            kv.append((None, line))  # preserve raw line
            continue
        key, val = line.split("=", 1)
        kv.append((key.strip(), val))
    return kv


def read_secret_file(path: Path) -> str | None:
    try:
        if path.exists():
            return path.read_text(encoding="utf-8").strip()
    except Exception:
        return None
    return None


def restore_env():
    lines = load_env_lines(ENV_FILE)
    if not lines:
        print(f"No .env found at {ENV_FILE}. Creating a new one from current content (if any)...")

    kv_pairs = parse_env(lines)

    # Build a mapping for current values
    current = {}
    for k, v in kv_pairs:
        if k is not None:
            current[k] = v

    # Collect replacement values
    replacements = {}
    for key, secret_path in KEY_TO_FILE.items():
        secret_val = read_secret_file(secret_path)
        if not secret_val:
            continue
        # Replace only if key missing or looks like placeholder
        if key not in current or is_placeholder(current.get(key, "")):
            replacements[key] = secret_val

    if not replacements:
        print("No keys to update from secrets (either already set or no secret files found).")
        return 0

    # Write backup
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = ENV_FILE.with_suffix(f".backup.{ts}")
    try:
        if ENV_FILE.exists():
            backup_path.write_text(ENV_FILE.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"Backed up existing .env to {backup_path}")
    except Exception as e:
        print(f"Warning: failed to write backup: {e}")

    # Apply updates preserving order and comments
    updated_lines: list[str] = []
    seen_keys: set[str] = set()
    for k, v in kv_pairs:
        if k is None:
            updated_lines.append(v)
            continue
        if k in replacements:
            updated_lines.append(f"{k}={replacements[k]}")
            seen_keys.add(k)
        else:
            updated_lines.append(f"{k}={v}")

    # Append any new keys not present previously
    for k, v in replacements.items():
        if k not in seen_keys and k not in current:
            updated_lines.append(f"{k}={v}")

    ENV_FILE.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")

    # Tighten permissions to 600
    try:
        os.chmod(ENV_FILE, 0o600)
    except Exception:
        pass

    print("Updated .env with secrets from files (secure values not printed).")
    print("Keys updated:", ", ".join(sorted(replacements.keys())))
    return 0


if __name__ == "__main__":
    sys.exit(restore_env())
