"""Generate a synthetic benchmark of food specification sheets.

Every document is a one-page A4 PDF with a known ground truth for the 14 EU
allergens and the nutrition panel. Allergen information is written in one of
ten formats observed in real supplier sheets, in Hungarian, English or
Polish. Each digital page can also be "scanned": rendered to an image,
rotated, blurred, noised and JPEG-compressed, so the OCR path is tested too.

    python evaluation/synth/generate.py --out data/synth --n 120 --seed 1 --scan-share 0.5

Label guide (same as for the real set, see docs/method.md):
* contains: named as an ingredient or declared as contained;
* traces: declared as "may contain" / cross-contamination;
* absent: the sheet declares the product free of it (table, global
  statement, or an allergen declaration that lists other allergens);
* unknown: the sheet says nothing about it.
"""

from __future__ import annotations

import argparse
import io
import json
import random
import sys
from pathlib import Path

from PIL import Image, ImageFilter
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vocab import ALLERGENS, PRODUCTS, ROWS, SHORT, T  # noqa: E402

FORMATS = [
    "statement", "global", "table_flags", "table_inx", "table_two_col",
    "checkbox_glyph", "checkbox_vector", "xmark", "grid", "none",
]
FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "/Library/Fonts/DejaVuSans.ttf",
]


def register_font() -> str:
    for p in FONT_PATHS:
        if Path(p).exists():
            pdfmetrics.registerFont(TTFont("DejaVu", p))
            bold = p.replace("DejaVuSans.ttf", "DejaVuSans-Bold.ttf")
            if Path(bold).exists():
                pdfmetrics.registerFont(TTFont("DejaVu-Bold", bold))
            else:
                pdfmetrics.registerFont(TTFont("DejaVu-Bold", p))
            return "DejaVu"
    raise SystemExit("DejaVuSans.ttf not found. Install fonts-dejavu-core.")


# ---------------------------------------------------------------------------
# Ground truth
# ---------------------------------------------------------------------------


def sample_truth(rng: random.Random, product: dict, fmt: str) -> dict[str, str]:
    contains = set(product["contains"])
    if fmt == "global":
        traces: set[str] = set()
    else:
        pool = [a for a in ALLERGENS if a not in contains]
        traces = set(rng.sample(pool, k=rng.choice([0, 0, 1, 1, 2])))
    if fmt in ("table_flags", "none"):
        traces = set()  # a single I/N column cannot express traces; "none" declares nothing
    truth = {}
    for a in ALLERGENS:
        if a in contains:
            truth[a] = "contains"
        elif a in traces:
            truth[a] = "traces"
        elif fmt == "none":
            truth[a] = "unknown"
        else:
            truth[a] = "absent"
    return truth


def sample_nutrition(rng: random.Random) -> dict[str, float]:
    fat = round(rng.uniform(0.2, 35), 1)
    sat = round(fat * rng.uniform(0.1, 0.6), 1)
    carb = round(rng.uniform(0, 75), 1)
    sug = round(carb * rng.uniform(0.0, 0.5), 1)
    prot = round(rng.uniform(0.5, 25), 1)
    salt = round(rng.uniform(0.01, 3.0), 2)
    kcal = round(9 * fat + 4 * carb + 4 * prot)
    kj = round(kcal * 4.184)
    return {"energy_kJ": kj, "energy_kcal": kcal, "fat_g": fat, "saturated_fat_g": sat,
            "carbohydrate_g": carb, "sugars_g": sug, "protein_g": prot, "salt_g": salt}


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


class Page:
    def __init__(self, path: Path, rng: random.Random):
        self.c = canvas.Canvas(str(path), pagesize=A4)
        self.w, self.h = A4
        self.rng = rng
        self.x = rng.uniform(45, 65)
        self.y = self.h - rng.uniform(50, 70)
        self.size = rng.choice([8.5, 9, 9.5, 10])

    def text(self, s: str, bold: bool = False, size: float | None = None, x: float | None = None,
             dy: float | None = None) -> None:
        size = size or self.size
        self.c.setFont("DejaVu-Bold" if bold else "DejaVu", size)
        self.c.drawString(self.x if x is None else x, self.y, s)
        self.y -= dy if dy is not None else size * 1.45

    def wrap(self, s: str, width: float = 470) -> None:
        words, line = s.split(), ""
        for w in words:
            cand = (line + " " + w).strip()
            if pdfmetrics.stringWidth(cand, "DejaVu", self.size) > width:
                self.text(line)
                line = w
            else:
                line = cand
        if line:
            self.text(line)

    def gap(self, k: float = 0.6) -> None:
        self.y -= self.size * k

    def save(self) -> None:
        self.c.showPage()
        self.c.save()


def fmt_num(v: float, dec: str) -> str:
    s = f"{v:g}" if isinstance(v, float) else str(v)
    return s.replace(".", dec)


def render(path: Path, rng: random.Random, lang: str, product: dict, fmt: str,
           truth: dict[str, str], nutrition: dict[str, float]) -> None:
    t = T[lang]
    pg = Page(path, rng)
    pg.text(t["title"], bold=True, size=pg.size + 4)
    pg.text(f"{t['maker']}: Example Foods Kft., 1234 Mintaváros", size=pg.size - 1)
    pg.gap()
    pg.text(f"{t['name']}: {product['name'][lang]}", bold=True)
    pg.gap()
    pg.text(t["desc"], bold=True)
    pg.wrap(t["desc_text"] + " " + rng.choice(t["distract"]))
    pg.gap()
    pg.text(t["ingr"], bold=True)
    pg.wrap(", ".join(product["ingredients"][lang]) + ".")
    pg.gap()
    pg.text(t["allerg"], bold=True)
    draw_allergens(pg, rng, lang, fmt, truth)
    pg.gap()
    pg.text(t["nutri"], bold=True)
    draw_nutrition(pg, lang, nutrition)
    pg.gap()
    pg.text(t["store"], bold=True)
    pg.text(t["store_text"])
    pg.save()


def _names(lang: str, keys: list[str]) -> str:
    return ", ".join(SHORT[lang][k] for k in keys)


def draw_allergens(pg: Page, rng: random.Random, lang: str, fmt: str, truth: dict[str, str]) -> None:
    t = T[lang]
    contains = [a for a in ALLERGENS if truth[a] == "contains"]
    traces = [a for a in ALLERGENS if truth[a] == "traces"]
    if fmt == "none":
        return
    if fmt in ("statement", "global"):
        if contains:
            pg.wrap(rng.choice(t["contains"]).format(l=_names(lang, contains)))
        else:
            pg.wrap(rng.choice(t["global"]))
        if traces:
            pg.wrap(rng.choice(t["traces"]).format(l=_names(lang, traces)))
        return
    rows = list(ALLERGENS)
    label_w = 270 if fmt.startswith("checkbox") else 300
    col0 = pg.x + label_w + rng.uniform(0, 25)
    step = rng.uniform(55, 75)
    small = pg.size - 0.5
    if fmt == "table_inx":
        pg.wrap(t["legend_inx"])
    if fmt in ("table_flags", "table_inx", "table_two_col", "xmark"):
        heads = {
            "table_flags": [t["flags_head"]],
            "table_inx": ["I / N / X"],
            "table_two_col": [t["present"], t["x_head"]],
            "xmark": [t["yes"], t["no"], t["x_head"]],
        }[fmt]
        for k, h in enumerate(heads):
            pg.c.setFont("DejaVu-Bold", small)
            pg.c.drawString(col0 + k * step, pg.y, h)
        pg.y -= small * 1.6
    if fmt == "grid":
        pg.text(t["grid_legend"], size=small)
        entries = [(i + 1, a) for i, a in enumerate(rows)]
        half = (len(entries) + 1) // 2
        for i in range(half):
            for j, col_x in ((i, pg.x), (i + half, pg.x + 250)):
                if j < len(entries):
                    n, a = entries[j]
                    sign = "+" if truth[a] in ("contains", "traces") else "-"
                    pg.c.setFont("DejaVu", small)
                    pg.c.drawString(col_x, pg.y, f"{n:02d} {sign} {SHORT[lang][a]}")
            pg.y -= small * 1.45
        return
    for a in rows:
        label = ROWS[lang][a]
        pg.c.setFont("DejaVu", small)
        # shrink long labels so they stay left of the columns
        size = small
        while pdfmetrics.stringWidth(label, "DejaVu", size) > label_w - 10 and size > 6:
            size -= 0.25
        pg.c.setFont("DejaVu", size)
        pg.c.drawString(pg.x, pg.y, label)
        st = truth[a]
        if fmt == "table_flags":
            yes, no = (t["yes"], t["no"]) if lang == "pl" or rng.random() < 0.3 else ("I", "N")
            if lang == "en" and yes == "I":
                yes, no = "Y", "N"
            pg.c.drawString(col0 + 10, pg.y, yes if st == "contains" else no)
        elif fmt == "table_inx":
            pg.c.drawString(col0 + 10, pg.y, {"contains": "I", "traces": "X"}.get(st, "N"))
        elif fmt == "table_two_col":
            pg.c.drawString(col0 + 10, pg.y, "I" if st == "contains" else "N")
            pg.c.drawString(col0 + step + 10, pg.y, "I" if st == "traces" else "N")
        elif fmt == "xmark":
            col = {"contains": 0, "absent": 1, "traces": 2}[st]
            pg.c.setFont("DejaVu-Bold", small + 1)
            pg.c.drawString(col0 + col * step + 8, pg.y, "X")
        elif fmt in ("checkbox_glyph", "checkbox_vector"):
            order = {"absent": 0, "contains": 1, "traces": 2}
            x = col0 - 20
            for k, lab in enumerate(t["cb"]):
                pg.c.setFont("DejaVu", small)
                pg.c.drawString(x, pg.y, lab)
                bx = x + pdfmetrics.stringWidth(lab, "DejaVu", small) + 3
                ticked = order[st] == k
                if fmt == "checkbox_glyph":
                    pg.c.drawString(bx, pg.y, "☒" if ticked else "☐")
                else:
                    s = small * 0.85
                    pg.c.rect(bx, pg.y - 1, s, s)
                    if ticked:
                        pg.c.line(bx, pg.y - 1, bx + s, pg.y - 1 + s)
                        pg.c.line(bx, pg.y - 1 + s, bx + s, pg.y - 1)
                x = bx + small + 12
        pg.y -= small * 1.55


def draw_nutrition(pg: Page, lang: str, n: dict[str, float]) -> None:
    t = T[lang]
    dec = t["dec"]
    lab = t["nut"]
    rows = [
        (lab[0], f"{n['energy_kJ']} kJ / {n['energy_kcal']} kcal"),
        (lab[1], f"{fmt_num(n['fat_g'], dec)} g"),
        (lab[2], f"{fmt_num(n['saturated_fat_g'], dec)} g"),
        (lab[3], f"{fmt_num(n['carbohydrate_g'], dec)} g"),
        (lab[4], f"{fmt_num(n['sugars_g'], dec)} g"),
        (lab[5], f"{fmt_num(n['protein_g'], dec)} g"),
        (lab[6], f"{fmt_num(n['salt_g'], dec)} g"),
    ]
    for k, v in rows:
        pg.c.setFont("DejaVu", pg.size)
        pg.c.drawString(pg.x, pg.y, k)
        pg.c.drawString(pg.x + 230, pg.y, v)
        pg.y -= pg.size * 1.45


# ---------------------------------------------------------------------------
# Simulated scanning
# ---------------------------------------------------------------------------

SCAN_LEVELS = {
    "scan_good": {"dpi": 200, "angle": 0.4, "blur": 0.3, "noise": 8, "jpeg": 85},
    "scan_poor": {"dpi": 150, "angle": 1.2, "blur": 0.7, "noise": 22, "jpeg": 55},
}


def scan(src: Path, dst: Path, level: str, rng: random.Random) -> None:
    from pdf2image import convert_from_path

    p = SCAN_LEVELS[level]
    img = convert_from_path(str(src), dpi=p["dpi"])[0].convert("L")
    img = img.rotate(rng.uniform(-p["angle"], p["angle"]), resample=Image.BICUBIC, fillcolor=255)
    img = img.filter(ImageFilter.GaussianBlur(p["blur"]))
    noise = Image.effect_noise(img.size, p["noise"])
    img = Image.blend(img, noise, 0.12 if level == "scan_poor" else 0.05)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=p["jpeg"])
    Image.open(buf).save(dst, "PDF", resolution=p["dpi"])


# ---------------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path("data/synth"))
    ap.add_argument("--n", type=int, default=120)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--scan-share", type=float, default=0.5, help="share of documents also scanned")
    args = ap.parse_args()

    register_font()
    rng = random.Random(args.seed)
    args.out.mkdir(parents=True, exist_ok=True)
    records = []
    for i in range(args.n):
        fmt = FORMATS[i % len(FORMATS)]
        lang = rng.choices(["hu", "en", "pl"], weights=[0.5, 0.25, 0.25])[0]
        pool = [p for p in PRODUCTS if not p["contains"]] if fmt == "global" else PRODUCTS
        product = rng.choice(pool)
        truth = sample_truth(rng, product, fmt)
        nutrition = sample_nutrition(rng)
        doc_id = f"s{args.seed}_{i:04d}"
        digital = args.out / f"{doc_id}_digital.pdf"
        render(digital, rng, lang, product, fmt, truth, nutrition)
        variants = {"digital": digital.name}
        if rng.random() < args.scan_share:
            for level in SCAN_LEVELS:
                dst = args.out / f"{doc_id}_{level}.pdf"
                scan(digital, dst, level, rng)
                variants[level] = dst.name
        records.append({"id": doc_id, "format": fmt, "language": lang,
                        "product": product["name"]["en"], "files": variants,
                        "allergens": truth, "nutrition": nutrition})
    with open(args.out / "labels.jsonl", "w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(records)} documents to {args.out}")


if __name__ == "__main__":
    main()
