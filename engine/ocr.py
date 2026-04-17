"""
engine/ocr.py
InvoiceIQ — W1: OCR Pipeline
Extracts structured fields from Indian GST invoices (digital PDF or scanned image)
into a clean pandas DataFrame.
"""

import re
import logging
from pathlib import Path
from typing import Optional
import pandas as pd
import pdfplumber
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import cv2
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Regex patterns for Indian GST invoice fields
# ---------------------------------------------------------------------------
PATTERNS = {
    # GSTIN: 15-char alphanumeric (2-digit state code + PAN + entity type + check)
    "gstin_supplier": re.compile(
        r"(?:supplier|seller|from|our\s+gstin)[^\n]*?:?\s*([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})",
        re.IGNORECASE,
    ),
    "gstin_buyer": re.compile(
        r"(?:buyer|recipient|bill\s+to|customer)[^\n]*?:?\s*([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})",
        re.IGNORECASE,
    ),
    # Fallback: any GSTIN in document
    "gstin_any": re.compile(
        r"\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b"
    ),
    # Invoice number
    "invoice_number": re.compile(
        r"(?:invoice\s*(?:no|number|#)|inv\.?\s*no\.?)\s*[:\-]?\s*([A-Z0-9\-\/]+)",
        re.IGNORECASE,
    ),
    # Invoice date (supports DD/MM/YYYY, DD-MM-YYYY, DD MMM YYYY)
    "invoice_date": re.compile(
        r"(?:invoice\s*date|date\s*of\s*invoice|date)[^\n]*?[:\-]?\s*"
        r"(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{4})",
        re.IGNORECASE,
    ),
    # Taxable / subtotal amount
    "taxable_amount": re.compile(
        r"(?:taxable\s*(?:value|amount)|subtotal|sub\s*total)[^\n]*?[:\-]?\s*(?:INR|Rs\.?|₹)?\s*([\d,]+\.?\d*)",
        re.IGNORECASE,
    ),
    # CGST
    "cgst_rate": re.compile(r"CGST\s*@?\s*([\d\.]+)\s*%", re.IGNORECASE),
    "cgst_amount": re.compile(
        r"CGST[^\n]*?(?:INR|Rs\.?|₹)\s*([\d,]+\.?\d*)", re.IGNORECASE
    ),
    # SGST / UTGST
    "sgst_rate": re.compile(r"(?:UTGST|SGST)\s*@?\s*([\d\.]+)\s*%", re.IGNORECASE),
    "sgst_amount": re.compile(
        r"(?:SGST|UTGST)[^\n]*?(?:INR|Rs\.?|₹)\s*([\d,]+\.?\d*)", re.IGNORECASE
    ),
    # IGST
    "igst_rate": re.compile(r"IGST\s*@?\s*([\d\.]+)\s*%", re.IGNORECASE),
    "igst_amount": re.compile(
        r"IGST[^\n]*?(?:INR|Rs\.?|₹)\s*([\d,]+\.?\d*)", re.IGNORECASE
    ),
    # Grand total
    "total_amount": re.compile(
        r"(?:grand\s*total|total\s*amount|amount\s*payable|net\s*payable)[^\n]*?(?:INR|Rs\.?|₹)?\s*([\d,]+\.?\d*)",
        re.IGNORECASE,
    ),
    # HSN / SAC code (4–8 digit product/service code)
    "hsn_code": re.compile(r"(?:HSN|SAC)\s*(?:code|/SAC)?[:\s]*(\d{4,8})", re.IGNORECASE),
    # Place of supply (state name or 2-digit state code)
    "place_of_supply": re.compile(
        r"place\s*of\s*supply[:\s]*([A-Za-z\s]+?)(?:\n|,|\d)", re.IGNORECASE
    ),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_amount(raw: str) -> Optional[float]:
    """Strip commas and convert to float."""
    try:
        return float(raw.replace(",", "").strip())
    except (ValueError, AttributeError):
        return None


def _first_match(pattern: re.Pattern, text: str, group: int = 1) -> Optional[str]:
    m = pattern.search(text)
    if m:
        # Handle patterns with alternation groups
        for g in range(1, m.lastindex + 1 if m.lastindex else 2):
            try:
                val = m.group(g)
                if val:
                    return val.strip()
            except IndexError:
                pass
    return None


def _detect_transaction_type(fields: dict) -> str:
    """
    Intra-state → CGST + SGST present; Inter-state → IGST present.
    Falls back to 'unknown' if neither detected.
    """
    if fields.get("igst_amount"):
        return "inter-state"
    if fields.get("cgst_amount") or fields.get("sgst_amount"):
        return "intra-state"
    return "unknown"


# ---------------------------------------------------------------------------
# Text extraction strategies
# ---------------------------------------------------------------------------

def extract_text_pdfplumber(pdf_path: str) -> str:
    """Best for digital/text-layer PDFs."""
    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
    return "\n".join(text_parts)


def extract_text_pymupdf(pdf_path: str) -> str:
    """Fallback for PDFs where pdfplumber yields thin output."""
    doc = fitz.open(pdf_path)
    return "\n".join(page.get_text() for page in doc)


def preprocess_image(img_array: np.ndarray) -> np.ndarray:
    """Denoise + binarize for better Tesseract accuracy."""
    gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary


def extract_text_tesseract(image_path: str) -> str:
    """OCR for scanned invoice images."""
    img = cv2.imread(image_path)
    processed = preprocess_image(img)
    pil_img = Image.fromarray(processed)
    # PSM 6: assume uniform block of text (good for invoices)
    return pytesseract.image_to_string(pil_img, lang="eng", config="--psm 6")


def extract_text_from_scanned_pdf(pdf_path: str) -> str:
    """Render each PDF page to image, then OCR."""
    doc = fitz.open(pdf_path)
    texts = []
    for page in doc:
        pix = page.get_pixmap(dpi=300)
        img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width, pix.n
        )
        if pix.n == 4:  # RGBA → BGR
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
        processed = preprocess_image(img_array)
        pil_img = Image.fromarray(processed)
        texts.append(pytesseract.image_to_string(pil_img, lang="eng", config="--psm 6"))
    return "\n".join(texts)


# ---------------------------------------------------------------------------
# Field extractor
# ---------------------------------------------------------------------------

def extract_fields(text: str, source_file: str) -> dict:
    """Run all regex patterns against extracted text and return a flat dict."""
    f = {"source_file": Path(source_file).name, "raw_text_length": len(text)}

    f["invoice_number"] = _first_match(PATTERNS["invoice_number"], text)
    f["invoice_date"] = _first_match(PATTERNS["invoice_date"], text)
    f["place_of_supply"] = _first_match(PATTERNS["place_of_supply"], text)
    f["hsn_code"] = _first_match(PATTERNS["hsn_code"], text)

    # GSTINs — try specific labels first, fall back to any GSTIN found
    f["gstin_supplier"] = _first_match(PATTERNS["gstin_supplier"], text)
    f["gstin_buyer"] = _first_match(PATTERNS["gstin_buyer"], text)
    if not f["gstin_supplier"] and not f["gstin_buyer"]:
        all_gstins = PATTERNS["gstin_any"].findall(text)
        f["gstin_supplier"] = all_gstins[0] if len(all_gstins) > 0 else None
        f["gstin_buyer"] = all_gstins[1] if len(all_gstins) > 1 else None

    # Amounts
    f["taxable_amount"] = _clean_amount(_first_match(PATTERNS["taxable_amount"], text) or "")
    f["cgst_rate"] = _clean_amount(_first_match(PATTERNS["cgst_rate"], text) or "")
    f["cgst_amount"] = _clean_amount(_first_match(PATTERNS["cgst_amount"], text) or "")
    f["sgst_rate"] = _clean_amount(_first_match(PATTERNS["sgst_rate"], text) or "")
    f["sgst_amount"] = _clean_amount(_first_match(PATTERNS["sgst_amount"], text) or "")
    f["igst_rate"] = _clean_amount(_first_match(PATTERNS["igst_rate"], text) or "")
    f["igst_amount"] = _clean_amount(_first_match(PATTERNS["igst_amount"], text) or "")
    f["total_amount"] = _clean_amount(_first_match(PATTERNS["total_amount"], text) or "")

    f["transaction_type"] = _detect_transaction_type(f)

    # Derived: total tax
    cgst = f["cgst_amount"] or 0
    sgst = f["sgst_amount"] or 0
    igst = f["igst_amount"] or 0
    f["total_tax"] = (cgst + sgst + igst) or None

    return f


# ---------------------------------------------------------------------------
# Main pipeline entry point
# ---------------------------------------------------------------------------

def process_invoice(file_path: str) -> dict:
    """
    Auto-detect file type, extract text with best available strategy,
    parse fields, return structured dict.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()
    text = ""

    if suffix == ".pdf":
        text = extract_text_pdfplumber(file_path)
        if len(text.strip()) < 50:  # likely scanned PDF
            logger.info(f"Low text yield from pdfplumber for {path.name}. Trying PyMuPDF...")
            text = extract_text_pymupdf(file_path)
        if len(text.strip()) < 50:  # still thin → OCR
            logger.info(f"Falling back to Tesseract OCR for {path.name}...")
            text = extract_text_from_scanned_pdf(file_path)

    elif suffix in {".png", ".jpg", ".jpeg", ".tiff", ".bmp"}:
        text = extract_text_tesseract(file_path)

    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    if not text.strip():
        logger.warning(f"No text extracted from {path.name}")

    return extract_fields(text, file_path)


def process_invoice_folder(folder_path: str) -> pd.DataFrame:
    """
    Process all invoices in a folder. Returns a DataFrame — one row per invoice.
    Use this as the output of W1 that feeds W2 and W3.
    """
    folder = Path(folder_path)
    supported = {".pdf", ".png", ".jpg", ".jpeg", ".tiff"}
    files = [f for f in folder.iterdir() if f.suffix.lower() in supported]

    if not files:
        raise FileNotFoundError(f"No supported invoice files in {folder_path}")

    records = []
    for f in files:
        logger.info(f"Processing: {f.name}")
        try:
            record = process_invoice(str(f))
            records.append(record)
        except Exception as e:
            logger.error(f"Failed to process {f.name}: {e}")
            records.append({"source_file": f.name, "error": str(e)})

    df = pd.DataFrame(records)
    # Reorder columns for readability
    priority_cols = [
        "source_file", "invoice_number", "invoice_date", "gstin_supplier",
        "gstin_buyer", "place_of_supply", "transaction_type", "taxable_amount",
        "cgst_rate", "cgst_amount", "sgst_rate", "sgst_amount",
        "igst_rate", "igst_amount", "total_tax", "total_amount", "hsn_code",
    ]
    existing = [c for c in priority_cols if c in df.columns]
    extra = [c for c in df.columns if c not in priority_cols]
    return df[existing + extra]