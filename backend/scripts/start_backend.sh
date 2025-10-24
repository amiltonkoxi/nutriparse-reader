export OCR_LANG=${OCR_LANG:-hun+eng}
export OCR_DPI=${OCR_DPI:-300}
#!/usr/bin/env bash
set -euo pipefail
ROOT="/home/kingterabyte/nutriparse-reader/backend"
API="http://127.0.0.1:8000"
cd "$ROOT"
# ativa venv
source .venv/bin/activate

mkdir -p ../tmp

# já está rodando?
if [ -f ../tmp/backend.pid ]; then
  PID=$(cat ../tmp/backend.pid || true)
  if [ -n "${PID:-}" ] && ps -p "$PID" >/dev/null 2>&1; then
    echo "↪️  Backend já está rodando (PID $PID)."
    exit 0
  fi
fi

# liberar porta 8000 (sem matar outros acidentalmente)
fuser -k 8000/tcp 2>/dev/null || true

# resolver caminho do uvicorn da VENV
UV=$(python - <<'PY'
import shutil; print(shutil.which("uvicorn"))
PY
)

# iniciar SEM --reload (mais estável em background)
nohup "$UV" app.main:app --host 0.0.0.0 --port 8000 > ../tmp/backend.log 2>&1 &
echo $! > ../tmp/backend.pid

# aguardar saúde
for i in {1..30}; do
  if curl -fsS "$API/health" >/dev/null 2>&1; then
    echo "✅ Backend UP (PID $(cat ../tmp/backend.pid))"
    exit 0
  fi
  sleep 0.5
done

echo "❌ Backend não respondeu. Últimas linhas:"
tail -n 80 ../tmp/backend.log || true
exit 1
