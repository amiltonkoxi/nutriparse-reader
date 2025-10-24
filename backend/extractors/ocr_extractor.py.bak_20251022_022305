# legend: OCR fallback using pdf2image + Tesseract (with progress prints).

from pdf2image import convert_from_path
import pytesseract
import tempfile

def extract_text_via_ocr(path: str, lang: str = "eng+hun+pol") -> str:
    """
    Convert PDF pages to images and OCR them with Tesseract.
    Uses dpi=200 to keep it reasonably fast.
    """
    chunks = []
    with tempfile.TemporaryDirectory() as tmpdir:
        images = convert_from_path(path, output_folder=tmpdir, fmt="png", dpi=200)
        total = len(images)
        for i, img in enumerate(images, 1):
            print(f"[OCR] Processing page {i}/{total}…")
            chunks.append(f"\n--- page {i} ---\n")
            chunks.append(pytesseract.image_to_string(img, lang=lang))
    return "".join(chunks).strip()
