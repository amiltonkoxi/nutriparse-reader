# legend: Extract selectable text via pdfplumber.

import pdfplumber

def extract_text_from_pdf(path: str) -> str:
    text = []
    try:
        with pdfplumber.open(path) as pdf:
            for p in pdf.pages:
                text.append(p.extract_text() or "")
    except Exception as e:
        print(f"[text_extractor] {e}")
    return "\n".join(text).strip()
