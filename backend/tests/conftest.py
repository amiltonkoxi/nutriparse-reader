from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))


@pytest.fixture
def spec_pdf(tmp_path):
    """A small digital specification sheet with a known answer."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas

    font = "Helvetica"
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/dejavu/DejaVuSans.ttf"):
        if Path(p).exists():
            pdfmetrics.registerFont(TTFont("DejaVu", p))
            font = "DejaVu"
            break
    path = tmp_path / "spec.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    c.setFont(font, 10)
    y = 800
    for line in [
        "TERMÉKSPECIFIKÁCIÓ",
        "Termék neve: Szezámmagos kenyér",
        "Összetevők: búzaliszt, ivóvíz, élesztő, étkezési só, szezámmag (4%).",
        "Allergén információ: a termék glutént és szezámmagot tartalmaz.",
        "Nyomokban tejet tartalmazhat.",
        "Átlagos tápérték 100 g termékben",
        "Energia 1100 kJ / 262 kcal",
        "Zsír 3,2 g",
        "amelyből telített zsírsavak 0,6 g",
        "Szénhidrát 48 g",
        "amelyből cukrok 2,1 g",
        "Fehérje 9,5 g",
        "Só 1,2 g",
    ]:
        c.drawString(50, y, line)
        y -= 16
    c.showPage()
    c.save()
    return path
