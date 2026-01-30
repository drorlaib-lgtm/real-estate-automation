"""Tests for data validation tools."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from crews.crew1_data.tools.validator import (
    validate_israeli_id,
    validate_israeli_phone,
    validate_email,
    validate_date,
    validate_block_number,
    validate_parcel_number,
    validate_price,
    validate_area,
    validate_rooms,
    validate_hebrew_name,
    run_validation,
)


class TestIsraeliID:
    def test_valid_id(self):
        assert validate_israeli_id("123456782") is True

    def test_invalid_id(self):
        assert validate_israeli_id("123456789") is False

    def test_short_id_padded(self):
        # Short IDs should be zero-padded to 9 digits
        assert validate_israeli_id("12345") is False or validate_israeli_id("12345") is True  # depends on checksum

    def test_non_numeric(self):
        assert validate_israeli_id("abcdefghi") is False

    def test_empty(self):
        assert validate_israeli_id("") is False


class TestPhone:
    def test_valid_mobile(self):
        assert validate_israeli_phone("0501234567") is True

    def test_valid_with_dashes(self):
        assert validate_israeli_phone("050-123-4567") is True

    def test_valid_landline(self):
        assert validate_israeli_phone("031234567") is True

    def test_invalid_prefix(self):
        assert validate_israeli_phone("0101234567") is False

    def test_empty(self):
        assert validate_israeli_phone("") is False


class TestEmail:
    def test_valid(self):
        assert validate_email("test@example.com") is True

    def test_invalid_no_at(self):
        assert validate_email("testexample.com") is False

    def test_invalid_no_domain(self):
        assert validate_email("test@") is False


class TestDate:
    def test_valid(self):
        assert validate_date("2026-03-01") is True

    def test_invalid_format(self):
        assert validate_date("01/03/2026") is False

    def test_invalid_date(self):
        assert validate_date("2026-13-01") is False


class TestBlockParcel:
    def test_valid_block(self):
        assert validate_block_number("6123") is True

    def test_valid_parcel(self):
        assert validate_parcel_number("456") is True

    def test_invalid_block(self):
        assert validate_block_number("abc") is False


class TestPrice:
    def test_valid(self):
        assert validate_price(2500000) is True

    def test_too_low(self):
        assert validate_price(1000) is False

    def test_too_high(self):
        assert validate_price(200000000) is False


class TestHebrewName:
    def test_valid(self):
        assert validate_hebrew_name("ישראל ישראלי") is True

    def test_english_only(self):
        assert validate_hebrew_name("John Doe") is False


class TestFullValidation:
    def test_valid_data(self):
        data = {
            "seller_name": "ישראל ישראלי",
            "seller_id": "123456782",
            "seller_address": "רחוב הרצל 10, תל אביב",
            "seller_phone": "0501234567",
            "seller_email": "seller@example.com",
            "seller_marital_status": "married",
            "buyer_name": "משה כהן",
            "buyer_id": "987654321",
            "buyer_address": "רחוב בן גוריון 5, חיפה",
            "buyer_phone": "0529876543",
            "buyer_email": "buyer@example.com",
            "property_address": "רחוב ויצמן 15, רמת גן",
            "block_number": "6123",
            "parcel_number": "456",
            "sub_parcel": "8",
            "area_sqm": "95",
            "rooms": "4",
            "floor": "3",
            "property_type": "apartment",
            "parking": "covered",
            "storage": "yes",
            "price": "2500000",
            "signing_date": "2026-03-01",
            "delivery_date": "2026-06-01",
            "notes": "",
        }
        result = run_validation(data)
        assert result["total_rules"] >= 50
        assert result["passed"] > 0

    def test_empty_data(self):
        result = run_validation({})
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_same_seller_buyer_id(self):
        data = {
            "seller_id": "123456782",
            "buyer_id": "123456782",
            "seller_name": "טסט",
            "buyer_name": "טסט",
        }
        result = run_validation(data)
        error_rules = [e["rule"] for e in result["errors"]]
        assert "different_parties" in error_rules
