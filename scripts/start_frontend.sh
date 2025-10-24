#!/usr/bin/env bash
set -euo pipefail
ROOT="/home/kingterabyte/nutriparse-reader"
cd "$ROOT/frontend"

# matar 3000/3001 se tiver travado
lsof -t -i:3000 -i:3001 2>/dev/null | xargs -r kill -9

# garantir API base (ajusta se usar outra URL)
export NEXT_PUBLIC_API_BASE="http://127.0.0.1:8000"

# subir Next.js (turbopack)
npm run dev
