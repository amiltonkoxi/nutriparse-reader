"""PDF -> Document.

Each page is read from the PDF text layer. A page with almost no text is a
scan, so only that page goes through OCR. Mixed documents (a digital cover
page plus scanned annexes) are common in supplier specifications.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache

import pdfplumber

from .document import Document, Page, Word, group_lines

log = logging.getLogger(__name__)

MIN_TEXT_CHARS_PER_PAGE = int(os.getenv("NUTRIPARSE_MIN_TEXT_CHARS", "40"))
OCR_DPI = int(os.getenv("NUTRIPARSE_OCR_DPI", "300"))
WANTED_OCR_LANGS = ("hun", "pol", "eng")


class PdfError(ValueError):
    """The file could not be opened as a PDF."""


@lru_cache(maxsize=1)
def ocr_languages() -> str:
    """Tesseract language string limited to models that are installed."""
    try:
        import pytesseract

        available = set(pytesseract.get_languages(config=""))
    except Exception:  # tesseract missing
        return ""
    langs = [lang for lang in WANTED_OCR_LANGS if lang in available]
    missing = [lang for lang in WANTED_OCR_LANGS if lang not in available]
    if missing:
        log.warning("Tesseract models missing: %s (OCR quality will drop)", ", ".join(missing))
    return "+".join(langs)


def count_pages(path: str) -> int:
    try:
        with pdfplumber.open(path) as pdf:
            return len(pdf.pages)
    except Exception as exc:  # pdfminer raises many types
        raise PdfError(str(exc)) from exc


def load(path: str, force_ocr: bool = False) -> Document:
    try:
        pdf = pdfplumber.open(path)
    except Exception as exc:
        raise PdfError(str(exc)) from exc

    pages: list[Page] = []
    with pdf:
        for i, p in enumerate(pdf.pages, start=1):
            words = [
                Word(w["text"], float(w["x0"]), float(w["top"]), float(w["x1"]), float(w["bottom"]))
                for w in p.extract_words(keep_blank_chars=False, use_text_flow=False)
            ]
            n_chars = sum(len(w.text) for w in words)
            source = "text"
            width, height = float(p.width), float(p.height)
            image = None
            if force_ocr or n_chars < MIN_TEXT_CHARS_PER_PAGE:
                ocr_words, image = _ocr_page(path, i)
                if image is not None and (ocr_words or not words):
                    words, source = ocr_words, "ocr"
                    width, height = float(image.width), float(image.height)
                else:
                    image = None
            page = Page(i, width, height, source, words, image=image)
            page.lines = group_lines(words, i)
            pages.append(page)
    return Document(pages, source_path=path)


def render_page(doc: Document, page: Page, dpi: int = 150) -> bool:
    """Attach a rendered image to a digital page (for vector tick boxes)."""
    if page.image is not None:
        return True
    if not doc.source_path:
        return False
    try:
        from pdf2image import convert_from_path

        imgs = convert_from_path(doc.source_path, dpi=dpi, first_page=page.number, last_page=page.number)
    except Exception as exc:  # poppler missing or broken file
        log.warning("Could not render page %s: %s", page.number, exc)
        return False
    if not imgs:
        return False
    page.image = imgs[0].convert("L")
    page.image_scale = dpi / 72.0
    return True


def _ocr_page(path: str, page_no: int):
    """OCR one page. Returns (words, grayscale PIL image)."""
    langs = ocr_languages()
    if not langs:
        log.error("OCR requested but Tesseract is not available")
        return [], None
    import pytesseract
    from pdf2image import convert_from_path

    images = convert_from_path(path, dpi=OCR_DPI, first_page=page_no, last_page=page_no)
    if not images:
        return [], None
    img = images[0].convert("L")
    data = pytesseract.image_to_data(
        img, lang=langs, config="--psm 3", output_type=pytesseract.Output.DICT
    )
    words: list[Word] = []
    for txt, conf, x, y, w, h in zip(
        data["text"], data["conf"], data["left"], data["top"], data["width"], data["height"], strict=True
    ):
        txt = (txt or "").strip()
        if not txt:
            continue
        try:
            if float(conf) < 0 and txt not in {"X", "x"}:
                continue
        except ValueError:
            pass
        words.append(Word(txt, float(x), float(y), float(x + w), float(y + h)))
    return words, img
