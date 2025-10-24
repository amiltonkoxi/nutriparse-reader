#!/usr/bin/env bash
set -euo pipefail
ROOT="/home/kingterabyte/nutriparse-reader"

# parar frontend (3000/3001)
lsof -t -i:3000 -i:3001 2>/dev/null | xargs -r kill -9 || true

# parar backend
cd "$ROOT/backend"
if [ -x scripts/stop_backend.sh ]; then
  ./scripts/stop_backend.sh
else
  fuser -k 8000/tcp 2>/dev/null || true
fi
echo "✅ Tudo parado."
