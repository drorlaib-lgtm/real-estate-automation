"""OCR Document Processor - Extracts data from scanned real estate documents."""

import os
import json
import re
from typing import Optional

from crewai.tools import tool

try:
    from PIL import Image
    import pytesseract
except ImportError:
    pytesseract = None
    Image = None


def extract_text_from_image(image_path: str, lang: str = "heb+eng") -> str:
    """Extract text from an image file using OCR."""
    if pytesseract is None:
        return f"[OCR not available - pytesseract not installed. File: {image_path}]"
    if not os.path.exists(image_path):
        return f"[File not found: {image_path}]"
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img, lang=lang)
    return text


def parse_tabu_document(text: str) -> dict:
    """Parse extracted text from a Tabu (land registry) document."""
    data = {}

    block_match = re.search(r"גוש[:\s]*(\d+)", text)
    if block_match:
        data["block_number"] = block_match.group(1)

    parcel_match = re.search(r"חלקה[:\s]*(\d+)", text)
    if parcel_match:
        data["parcel_number"] = parcel_match.group(1)

    sub_parcel_match = re.search(r"תת[- ]?חלקה[:\s]*(\d+)", text)
    if sub_parcel_match:
        data["sub_parcel"] = sub_parcel_match.group(1)

    area_match = re.search(r"שטח[:\s]*([\d.]+)\s*(?:מ\"?ר|מטר)", text)
    if area_match:
        data["area_sqm"] = float(area_match.group(1))

    owner_match = re.search(r"(?:בעלים|שם הבעלים)[:\s]*(.+?)(?:\n|$)", text)
    if owner_match:
        data["registered_owner"] = owner_match.group(1).strip()

    mortgage_match = re.search(r"משכנתא|שעבוד", text)
    data["has_mortgage"] = bool(mortgage_match)

    lien_match = re.search(r"עיקול", text)
    data["has_lien"] = bool(lien_match)

    warning_match = re.search(r"הערת אזהרה", text)
    data["has_warning_note"] = bool(warning_match)

    rights_match = re.search(r"(?:זכויות|סוג הזכות)[:\s]*(.+?)(?:\n|$)", text)
    if rights_match:
        data["rights_type"] = rights_match.group(1).strip()

    return data


def parse_municipal_document(text: str) -> dict:
    """Parse extracted text from municipal/city records."""
    data = {}

    zone_match = re.search(r"(?:ייעוד|אזור)[:\s]*(.+?)(?:\n|$)", text)
    if zone_match:
        data["zoning"] = zone_match.group(1).strip()

    permit_match = re.search(r"היתר בנייה[:\s]*(.+?)(?:\n|$)", text)
    if permit_match:
        data["building_permit"] = permit_match.group(1).strip()

    violation_match = re.search(r"חריגות? בנייה|חריגה", text)
    data["has_violations"] = bool(violation_match)

    tax_match = re.search(r"(?:ארנונה|חיוב)[:\s]*([\d,.]+)", text)
    if tax_match:
        data["property_tax"] = tax_match.group(1)

    return data


@tool("process_document_ocr")
def process_document_ocr(
    image_path: str,
    document_type: str = "tabu",
) -> str:
    """Process a scanned document using OCR and extract structured data.
    document_type: 'tabu' for land registry, 'municipal' for city records.
    Returns extracted data as JSON string."""
    text = extract_text_from_image(image_path)

    if document_type == "tabu":
        extracted = parse_tabu_document(text)
    elif document_type == "municipal":
        extracted = parse_municipal_document(text)
    else:
        extracted = {"raw_text": text}

    extracted["source_file"] = image_path
    extracted["document_type"] = document_type
    extracted["raw_text_preview"] = text[:500]

    return json.dumps(extracted, ensure_ascii=False, indent=2)
