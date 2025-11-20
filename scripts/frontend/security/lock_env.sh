#!/bin/bash
# Lock or unlock .env files to prevent accidental overwrites (macOS/BSD chflags)
# Usage:
#   ./scripts/security/lock_env.sh lock   # makes .env files immutable
#   ./scripts/security/lock_env.sh unlock # removes immutability

set -e
cd "$(dirname "$0")/../.."

ACTION="$1"
if [ -z "$ACTION" ]; then
  echo "Usage: $0 [lock|unlock]"
  exit 1
fi

TARGETS=(
  ".env"
  "backend/.env"
)

lock_file() {
  local f="$1"
  if [ -f "$f" ]; then
    chflags uchg "$f" 2>/dev/null || true
    echo "Locked: $f"
  fi
}

unlock_file() {
  local f="$1"
  if [ -f "$f" ]; then
    chflags nouchg "$f" 2>/dev/null || true
    echo "Unlocked: $f"
  fi
}

case "$ACTION" in
  lock)
    for f in "${TARGETS[@]}"; do lock_file "$f"; done
    ;;
  unlock)
    for f in "${TARGETS[@]}"; do unlock_file "$f"; done
    ;;
  *)
    echo "Unknown action: $ACTION (use lock|unlock)"
    exit 1
    ;;
fi

echo "Done."