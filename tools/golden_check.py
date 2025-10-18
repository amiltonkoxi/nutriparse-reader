#!/usr/bin/env python3
"""
Compare current API outputs with golden/*.json.
Usage:
  python tools/golden_check.py [IN_DIR] [GOLDEN_DIR] [API_URL]
Defaults:
  IN_DIR=samples  GOLDEN_DIR=golden  API_URL=http://127.0.0.1:8000
"""
import os, sys, glob, json, difflib, requests

IN_DIR  = sys.argv[1] if len(sys.argv) > 1 else "samples"
GOLDEN  = sys.argv[2] if len(sys.argv) > 2 else "golden"
API     = sys.argv[3] if len(sys.argv) > 3 else "http://127.0.0.1:8000"

fails = 0
pdfs = sorted(glob.glob(os.path.join(IN_DIR, "*.pdf")))
for path in pdfs:
    name = os.path.splitext(os.path.basename(path))[0]
    golden_path = os.path.join(GOLDEN, f"{name}.json")
    if not os.path.exists(golden_path):
        print(f"[skip] no golden for {name}")
        continue

    with open(path, "rb") as fh:
        r = requests.post(f"{API}/api/extract",
                          files={"file": (os.path.basename(path), fh, "application/pdf")},
                          timeout=120)
    r.raise_for_status()
    cur = json.dumps(r.json(), ensure_ascii=False, indent=2, sort_keys=True)
    ref = json.dumps(json.load(open(golden_path, encoding="utf-8")),
                     ensure_ascii=False, indent=2, sort_keys=True)

    if cur != ref:
        fails += 1
        print(f"\n[diff] {name}.json differs from golden:")
        for line in difflib.unified_diff(ref.splitlines(), cur.splitlines(),
                                         fromfile="golden", tofile="current", lineterm=""):
            print(line)
    else:
        print(f"[ok] {name}.json matches golden")

print(f"\nSummary: {len(pdfs)} files checked, {fails} diffs.")
sys.exit(1 if fails else 0)
