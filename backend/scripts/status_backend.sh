#!/usr/bin/env bash
set -euo pipefail
PIDFILE="/home/kingterabyte/nutriparse-reader/backend/../tmp/backend.pid"
if [ -f "$PIDFILE" ]; then
  PID=$(cat "$PIDFILE" || true)
  if [ -n "${PID:-}" ] && ps -p "$PID" >/dev/null 2>&1; then
    echo "🏃 Backend rodando (PID $PID)"
    exit 0
  fi
fi
echo "⛔ Backend parado"
exit 1
