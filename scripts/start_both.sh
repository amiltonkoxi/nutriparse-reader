#!/usr/bin/env bash
set -euo pipefail
ROOT="/home/kingterabyte/nutriparse-reader"
cd "$ROOT/backend"

# 1) backend estável (sem --reload) usando scripts já criados
if [ ! -x scripts/start_backend.sh ]; then
  echo "Faltam scripts do backend. Rode-os primeiro ou crie novamente."
  exit 1
fi
./scripts/start_backend.sh

# 2) conferir saúde
curl -fsS http://127.0.0.1:8000/health >/dev/null || {
  echo "❌ Backend não respondeu. Veja os logs:"
  "$ROOT/backend/scripts/logs_backend.sh"
  exit 1
}

# 3) frontend (fica em primeiro plano para você ver)
cd "$ROOT"
exec ./scripts/start_frontend.sh
