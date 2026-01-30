"""Tests for OCR document processing tools."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from crews.crew1_data.tools.ocr_processor import parse_tabu_document, parse_municipal_document


class TestTabuParsing:
    def test_extract_block(self):
        text = "נסח טאבו\nגוש: 6123\nחלקה: 456"
        result = parse_tabu_document(text)
        assert result["block_number"] == "6123"
        assert result["parcel_number"] == "456"

    def test_extract_area(self):
        text = "שטח: 95.5 מ\"ר"
        result = parse_tabu_document(text)
        assert result["area_sqm"] == 95.5

    def test_detect_mortgage(self):
        text = "רשומה משכנתא לטובת בנק לאומי"
        result = parse_tabu_document(text)
        assert result["has_mortgage"] is True

    def test_detect_lien(self):
        text = "עיקול על הנכס"
        result = parse_tabu_document(text)
        assert result["has_lien"] is True

    def test_no_lien(self):
        text = "נסח נקי"
        result = parse_tabu_document(text)
        assert result["has_lien"] is False

    def test_extract_owner(self):
        text = "בעלים: ישראל ישראלי"
        result = parse_tabu_document(text)
        assert result["registered_owner"] == "ישראל ישראלי"


class TestMunicipalParsing:
    def test_extract_zoning(self):
        text = "ייעוד: מגורים א"
        result = parse_municipal_document(text)
        assert result["zoning"] == "מגורים א"

    def test_detect_violations(self):
        text = "נמצאו חריגות בנייה בנכס"
        result = parse_municipal_document(text)
        assert result["has_violations"] is True

    def test_no_violations(self):
        text = "הנכס תקין"
        result = parse_municipal_document(text)
        assert result["has_violations"] is False
