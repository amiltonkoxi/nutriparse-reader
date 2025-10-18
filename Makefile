# === NutriParse Reader — Developer shortcuts ===
API ?= http://127.0.0.1:8000
IN  ?= samples
OUT ?= out
GOLDEN ?= golden

.PHONY: help batch golden-check previews golden-freeze test clean

help:
	@echo "Usage:"
	@echo "  make batch           # Run extraction on all PDFs -> out/*.json + out/summary.csv"
	@echo "  make golden-check    # Compare API outputs with golden/*.json (regression test)"
	@echo "  make previews        # Save diagnostics.raw_text_preview -> out/*.txt"
	@echo "  make golden-freeze   # Copy current out/*.json into golden/ (freeze baseline)"
	@echo "  make test            # batch + golden-check"
	@echo "  make clean           # Remove out/ and temp files"
	@echo ""
	@echo "Vars (override like: make batch API=http://localhost:8000 IN=samples2):"
	@echo "  API=$(API)  IN=$(IN)  OUT=$(OUT)  GOLDEN=$(GOLDEN)"

batch:
	python tools/batch_extract.py $(IN) $(OUT) $(API)

golden-check:
	python tools/golden_check.py $(IN) $(GOLDEN) $(API)

previews:
	python tools/save_previews.py $(IN) $(OUT) $(API)

golden-freeze:
	@mkdir -p $(GOLDEN)
	@cp $(OUT)/*.json $(GOLDEN)/ 2>/dev/null || true
	@echo "Golden updated from $(OUT)/ -> $(GOLDEN)/"

test: batch golden-check

clean:
	rm -rf $(OUT)
	mkdir -p $(OUT)
	@echo "Cleaned $(OUT)/"
