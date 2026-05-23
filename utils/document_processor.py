import os
import fitz
import pytesseract
from PIL import Image


def extract_text_from_pdf(file_path: str) -> list[dict]:
    """
    Extract text from PDF.
    Falls back to OCR for scanned pages.
    Returns list of dicts with text, source, and page.
    """

    # FIX: prevent PyMuPDF crash on empty/missing file
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        return []

    pages = []

    try:
        doc = fitz.open(file_path)
    except Exception:
        return []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text().strip()

        # OCR fallback for scanned PDFs
        if not text:
            try:
                pix = page.get_pixmap()
                img = Image.frombytes(
                    "RGB",
                    [pix.width, pix.height],
                    pix.samples
                )

                try:
                    text = pytesseract.image_to_string(img)
                except pytesseract.TesseractNotFoundError:
                    text = ""

            except Exception:
                text = ""

        if text.strip():
            pages.append({
                "text": text,
                "source": os.path.basename(file_path),
                "page": page_num + 1
            })

    doc.close()
    return pages


def extract_text_from_image(file_path: str) -> list[dict]:
    """
    Extract text from image using OCR.
    Returns same format as PDF extraction.
    """

    # FIX: prevent empty image crash
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        return []

    try:
        img = Image.open(file_path)

        try:
            text = pytesseract.image_to_string(img)
        except pytesseract.TesseractNotFoundError:
            text = ""

        if not text.strip():
            return []

        return [{
            "text": text,
            "source": os.path.basename(file_path),
            "page": 1
        }]

    except Exception:
        return []


def process_uploaded_file(file_path: str) -> list[dict]:
    """
    Main entry point.
    Detects file type and routes correctly.
    """

    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        return []

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return extract_text_from_pdf(file_path)

    elif ext in [".png", ".jpg", ".jpeg"]:
        return extract_text_from_image(file_path)

    return []