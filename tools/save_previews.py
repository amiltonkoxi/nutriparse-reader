#!/usr/bin/env python3
"""
Save diagnostics.raw_text_preview for each PDF to out/*.txt
"""
import os, sys, glob, json, requests

IN_DIR  = sys.argv[1] if len(sys.argv) > 1 else "samples"
OUT_DIR = sys.argv[2] if len(sys.argv) > 2 else "out"
API     = sys.argv[3] if len(sys.argv) > 3 else "http://127.0.0.1:8000"

os.makedirs(OUT_DIR, exist_ok=True)
for path in glob.glob(os.path.join(IN_DIR, "*.pdf")):
    name = os.path.splitext(os.path.basename(path))[0]
    with open(path, "rb") as fh:
        r = requests.post(f"{API}/api/extract", files={"file": (os.path.basename(path), fh, "application/pdf")}, timeout=120)
    r.raise_for_status()
    data = r.json()
    text = (data.get("diagnostics") or {}).get("raw_text_preview") or ""
    open(os.path.join(OUT_DIR, f"{name}.txt"), "w", encoding="utf-8").write(text)
    print(f"[ok] {name}.txt")
print("Done.")
