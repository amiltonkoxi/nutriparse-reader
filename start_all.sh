#!/usr/bin/env bash
set -e

ROOT="/home/kingterabyte/nutriparse-reader"

# --- BACKEND ---
cd "$ROOT/backend"
source .venv/bin/activate
mkdir -p "$ROOT/tmp"
# mata porta 8000 se estiver ocupada
sudo lsof -t -i:8000 | xargs -r kill -9
# sobe uvicorn em background com log
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > "$ROOT/tmp/backend.log" 2>&1 &

# checa saúde
for i in {1..10}; do
  sleep 0.5
  if curl -fsS http://localhost:8000/health >/dev/null; then
    echo "Backend OK em http://localhost:8000"
    break
  fi
  if [ "$i" = 10 ]; then
    echo "Falha para subir backend, veja $ROOT/tmp/backend.log"; exit 1
  fi
done

# --- FRONTEND ---
cd "$ROOT/frontend"
export NEXT_PUBLIC_API_URL="http://localhost:8000"
# mata 3000/3001 se estiverem ocupadas
sudo lsof -t -i:3000 -i:3001 | xargs -r kill -9
npm run dev
