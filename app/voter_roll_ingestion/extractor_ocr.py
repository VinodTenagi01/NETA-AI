"""
OCR extraction from image-based PDF voter rolls.

ECI voter pages have a 3-column card grid (949×1343 px).
We split each page image into 3 vertical strips before OCR so Tesseract
processes one column at a time, giving clean single-voter-per-block output.

Tesseract: C:\Program Files\Tesseract-OCR\tesseract.exe
"""
from __future__ import annotations

from pathlib import Path

import pdfplumber
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Column split fractions for a 3-column voter page
# Measured from the actual 949-wide ECI voter roll pages
_COL_SPLITS = [0.0, 0.338, 0.662, 1.0]  # 3 equal-ish columns

# Header row height fraction (skip constituency/section header on voter pages)
# Set to 0.02 — a minimal skip to avoid the printed page border only.
# The column strips are already narrow enough to exclude wide page headers.
_HEADER_ROW_H = 0.02


def _setup_tesseract() -> None:
    if Path(TESSERACT_PATH).exists():
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


_setup_tesseract()


def _preprocess(img: Image.Image) -> Image.Image:
    img = img.convert("L")
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = img.filter(ImageFilter.SHARPEN)
    return img.convert("RGB")


def _page_to_pil(page) -> Image.Image | None:
    images = page.images
    if not images:
        return None
    info = images[0]
    try:
        raw = info["stream"].get_data()
        w, h = int(info["srcsize"][0]), int(info["srcsize"][1])
        if len(raw) == w * h * 3:
            return Image.frombytes("RGB", (w, h), raw)
        if len(raw) == w * h:
            return Image.frombytes("L", (w, h), raw).convert("RGB")
    except Exception:
        pass
    return None


def _ocr_columns(img: Image.Image, page_number: int) -> str:
    """
    For voter pages (page >= 3): split into 3 column strips, OCR each,
    join with a clear sentinel so the parser knows column boundaries.
    For header/photo pages: OCR the full image.
    """
    if page_number <= 2:
        img_pre = _preprocess(img)
        return pytesseract.image_to_string(img_pre, lang="eng")

    w, h = img.size
    skip_top = int(h * _HEADER_ROW_H)  # skip page header row
    col_texts: list[str] = []

    for i in range(3):
        x0 = int(w * _COL_SPLITS[i])
        x1 = int(w * _COL_SPLITS[i + 1])
        strip = img.crop((x0, skip_top, x1, h))
        strip = _preprocess(strip)
        text = pytesseract.image_to_string(strip, lang="eng")
        col_texts.append(text)

    # Join columns with a clear boundary marker
    return "\n---COLUMN_BREAK---\n".join(col_texts)


def extract_pages_ocr(pdf_path: Path) -> list[tuple[int, str]]:
    """
    Return [(page_number, ocr_text), ...] for all pages.
    Voter pages (3+) are OCR'd as 3 column strips.
    """
    results: list[tuple[int, str]] = []

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            img = _page_to_pil(page)
            if img is None:
                results.append((page_num, ""))
                continue
            try:
                text = _ocr_columns(img, page_num)
                results.append((page_num, text))
            except Exception as exc:
                results.append((page_num, f"OCR_ERROR: {exc}"))

    return results
