from __future__ import annotations
from typing import List
import re
from pdf2image import convert_from_path
from PIL import Image, ImageOps, ImageFilter
import pytesseract
from unidecode import unidecode

def _preprocess(img: Image.Image) -> Image.Image:
    img = ImageOps.grayscale(img)
    img = ImageOps.autocontrast(img)
    img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=80, threshold=3))
    img = img.point(lambda x: 255 if x > 180 else 0)
    return img

def _normalize(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    text = re.sub(r"(\d),(\d)", r"\1.\2", text)
    text = unidecode(text).lower()
    return text.strip()

def ocr_extract(pdf_path: str, dpi: int = 300) -> str:
    pages: List[Image.Image] = convert_from_path(pdf_path, dpi=dpi)
    texts: List[str] = []
    for img in pages:
        imgp = _preprocess(img)
        t = pytesseract.image_to_string(imgp, lang="eng+hun+pol")
        if t:
            texts.append(t)
    return _normalize("\n".join(texts))
