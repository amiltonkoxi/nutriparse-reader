#!/usr/bin/env python3
"""
Batch-extract PDFs -> JSON + CSV summary.

Usage:
  python tools/batch_extract.py [IN_DIR] [OUT_DIR] [API_URL]
Defaults:
  IN_DIR=samples   OUT_DIR=out    API_URL=http://127.0.0.1:8000
"""
import os, sys, glob, json, csv, time
import requests

IN_DIR  = sys.argv[1] if len(sys.argv) > 1 else "samples"
OUT_DIR = sys.argv[2] if len(sys.argv) > 2 else "out"
API     = sys.argv[3] if len(sys.argv) > 3 else "http://127.0.0.1:8000"

os.makedirs(OUT_DIR, exist_ok=True)

rows = []
pdfs = sorted(glob.glob(os.path.join(IN_DIR, "*.pdf")))
if not pdfs:
    print(f"[warn] no PDFs in {IN_DIR}/")
    sys.exit(0)

for i, path in enumerate(pdfs, 1):
    name = os.path.splitext(os.path.basename(path))[0]
    t0 = time.time()
    try:
        with open(path, "rb") as fh:
            r = requests.post(f"{API}/api/extract", files={"file": (os.path.basename(path), fh, "application/pdf")}, timeout=120)
        r.raise_for_status()
        data = r.json()

        # save raw JSON
        out_path = os.path.join(OUT_DIR, f"{name}.json")
        with open(out_path, "w", encoding="utf-8") as fp:
            json.dump(data, fp, ensure_ascii=False, indent=2)

        meta = data.get("meta", {})
        nut  = data.get("nutrition", {}) or {}
        eng  = nut.get("energy") or {}
        row = {
            "file": os.path.basename(path),
            "mode": meta.get("extraction_mode"),
            "confidence": meta.get("confidence"),
            "kJ": eng.get("kJ"),
            "kcal": eng.get("kcal"),
            "fat_g": nut.get("fat_g"),
            "carb_g": nut.get("carbohydrate_g"),
            "sugar_g": nut.get("sugar_g"),
            "protein_g": nut.get("protein_g"),
            "salt_g": nut.get("salt_g"),
        }
        rows.append(row)
        dt = time.time() - t0
        print(f"[{i}/{len(pdfs)}] {name} -> OK ({dt:.2f}s)")
    except Exception as e:
        print(f"[{i}/{len(pdfs)}] {name} -> ERROR: {e}")

# write CSV summary
csv_path = os.path.join(OUT_DIR, "summary.csv")
with open(csv_path, "w", newline="", encoding="utf-8") as fp:
    fieldnames = ["file","mode","confidence","kJ","kcal","fat_g","carb_g","sugar_g","protein_g","salt_g"]
    w = csv.DictWriter(fp, fieldnames=fieldnames)
    w.writeheader()
    for row in rows:
        w.writerow(row)

print(f"\nDone. JSONs in {OUT_DIR}/  |  CSV: {csv_path}")
