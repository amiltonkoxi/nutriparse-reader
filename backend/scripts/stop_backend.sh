#!/usr/bin/env bash
set -euo pipefail
PIDFILE="/home/kingterabyte/nutriparse-reader/backend/../tmp/backend.pid"
if [ -f "$PIDFILE" ]; then
  PID=$(cat "$PIDFILE" || true)
  if [ -n "${PID:-}" ] && ps -p "$PID" >/dev/null 2>&1; then
    echo "🛑 Parando backend (PID $PID)..."
    kill "$PID" || true
    sleep 1
    if ps -p "$PID" >/dev/null 2>&1; then
      echo "⚠️  ainda vivo; aplicando -9"
      kill -9 "$PID" || true
    fi
  fi
  rm -f "$PIDFILE"
fi
# garantir porta livre
fuser -k 8000/tcp 2>/dev/null || true
echo "✅ Backend parado."
