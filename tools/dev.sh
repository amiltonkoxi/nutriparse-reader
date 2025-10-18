#!/usr/bin/env bash
set -euo pipefail

# paths
BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/backend"
FRONTEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/frontend"

# encerra tudo quando apertar Ctrl+C
trap "kill 0" INT TERM EXIT

echo "🚀 Starting NutriParse Reader (backend + frontend)..."

# backend
echo "▶ Backend: uvicorn running at http://127.0.0.1:8000"
( cd "$BACKEND_DIR" && source .venv/bin/activate && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 ) &

# pequena pausa para garantir inicialização
sleep 2

# frontend
echo "▶ Frontend: Next.js running at http://localhost:3000"
( cd "$FRONTEND_DIR" && npm run dev )

