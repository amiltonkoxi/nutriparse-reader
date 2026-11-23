# NutriParse developer commands. Run `make help`.
PY      ?= python3
VENV    ?= backend/.venv
BIN      = $(VENV)/bin
N       ?= 120
SEED    ?= 2
REAL    ?=

.PHONY: help install dev api web test lint bench bench-digital bench-real docker clean

help:
	@echo "make install        create backend/.venv and install backend + frontend deps"
	@echo "make dev            run API (:8000) and web app (:3000)"
	@echo "make test           unit and API tests"
	@echo "make lint           ruff"
	@echo "make bench          synthetic benchmark (digital + scanned), N=$(N) SEED=$(SEED)"
	@echo "make bench-digital  fast benchmark, digital PDFs only (used in CI)"
	@echo "make bench-real REAL=/path/to/pdfs   private real-world set"
	@echo "make docker         build the API image"

install:
	$(PY) -m venv $(VENV)
	$(BIN)/pip install -r backend/requirements-dev.txt
	cd frontend && npm ci

api:
	cd backend && ../$(BIN)/uvicorn nutriparse.api:app --reload --port 8000

web:
	cd frontend && NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000 npm run dev

dev:
	$(MAKE) -j2 api web

test:
	cd backend && ../$(BIN)/pytest -q

lint:
	cd backend && ../$(BIN)/ruff check nutriparse tests ../evaluation

data/synth_seed$(SEED)/labels.jsonl:
	$(BIN)/python evaluation/synth/generate.py --out data/synth_seed$(SEED) --n $(N) --seed $(SEED) --scan-share 0.4

bench: data/synth_seed$(SEED)/labels.jsonl
	$(BIN)/python evaluation/evaluate.py synth --data data/synth_seed$(SEED) --out evaluation/results/synth_seed$(SEED)

bench-digital: data/synth_seed$(SEED)/labels.jsonl
	$(BIN)/python evaluation/evaluate.py synth --data data/synth_seed$(SEED) --variants digital \
		--out evaluation/results/synth_seed$(SEED)_digital

bench-real:
	@test -n "$(REAL)" || (echo "usage: make bench-real REAL=/path/to/pdfs" && exit 1)
	$(BIN)/python evaluation/evaluate.py real --data $(REAL) --out evaluation/results/real

docker:
	docker build -t nutriparse-api backend

clean:
	rm -rf data/synth_seed* backend/.pytest_cache backend/.ruff_cache
