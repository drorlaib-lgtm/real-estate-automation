"""Tests for data adapter (format conversion between nested and flat)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.data_adapter import normalize_transaction, denormalize_transaction


NESTED_DATA = {
    "sellers": [
        {
            "name": "הנשיא המלך",
            "id": "01208374",
            "address": "דרוב לייב",
            "phone": "054675397",
            "email": "f@jac.com",
            "marital_status": "married",
        }
    ],
    "buyers": [
        {
            "name": "מאיר המלך",
            "id": "20754853",
            "address": "המלך 1 הרצליה",
            "phone": "054655932",
            "email": "meir@king.com",
            "marital_status": "married",
        }
    ],
    "property": {
        "address": "ברנבאו",
        "block_number": "777",
        "parcel_number": "444",
        "sub_parcel": "1",
        "area_sqm": 1500,
        "rooms": 8.5,
        "floor": 10,
        "property_type": "apartment",
        "parking": "underground",
        "storage": "yes",
    },
    "transaction": {
        "price": 2200000,
        "signing_date": "2026-02-24",
        "delivery_date": "2026-05-10",
    },
    "seller_notes": "הערות טסט",
}

FLAT_DATA = {
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
    "property_address": "רחוב ויצמן 15, דירה 8, רמת גן",
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
    "notes": "הערות",
}


class TestNormalizeTransaction:
    def test_nested_to_flat(self):
        flat = normalize_transaction(NESTED_DATA)
        assert flat["seller_name"] == "הנשיא המלך"
        assert flat["seller_id"] == "01208374"
        assert flat["buyer_name"] == "מאיר המלך"
        assert flat["property_address"] == "ברנבאו"
        assert flat["block_number"] == "777"
        assert flat["price"] == "2200000"
        assert flat["signing_date"] == "2026-02-24"
        assert flat["notes"] == "הערות טסט"

    def test_flat_passes_through(self):
        result = normalize_transaction(FLAT_DATA)
        assert result["seller_name"] == "ישראל ישראלי"
        assert result is FLAT_DATA  # Should return same dict

    def test_empty_data(self):
        flat = normalize_transaction({})
        assert flat.get("seller_name", "") == ""
        assert flat.get("buyer_name", "") == ""

    def test_multiple_sellers(self):
        data = {
            "sellers": [
                {"name": "מוכר1", "id": "111", "address": "", "phone": "", "email": "", "marital_status": ""},
                {"name": "מוכר2", "id": "222", "address": "", "phone": "", "email": "", "marital_status": ""},
            ],
            "buyers": [
                {"name": "קונה1", "id": "333", "address": "", "phone": "", "email": "", "marital_status": ""},
                {"name": "קונה2", "id": "444", "address": "", "phone": "", "email": "", "marital_status": ""},
            ],
            "property": {},
            "transaction": {},
        }
        flat = normalize_transaction(data)
        # Primary seller is first
        assert flat["seller_name"] == "מוכר1"
        assert flat["seller_id"] == "111"
        # Secondary seller fields should be populated
        assert flat["seller2_name"] == "מוכר2"
        assert flat["seller2_id"] == "222"
        # Primary buyer is first
        assert flat["buyer_name"] == "קונה1"
        assert flat["buyer_id"] == "333"
        # Secondary buyer fields should be populated
        assert flat["buyer2_name"] == "קונה2"
        assert flat["buyer2_id"] == "444"
        # All sellers/buyers preserved
        assert len(flat["all_sellers"]) == 2
        assert len(flat["all_buyers"]) == 2


class TestDenormalizeTransaction:
    def test_flat_to_nested(self):
        nested = denormalize_transaction(FLAT_DATA)
        assert nested["sellers"][0]["name"] == "ישראל ישראלי"
        assert nested["buyers"][0]["name"] == "משה כהן"
        assert nested["property"]["address"] == "רחוב ויצמן 15, דירה 8, רמת גן"
        assert nested["transaction"]["price"] == 2500000
        assert nested["transaction"]["signing_date"] == "2026-03-01"

    def test_roundtrip_nested(self):
        """Nested -> flat -> nested should preserve key data."""
        flat = normalize_transaction(NESTED_DATA)
        nested = denormalize_transaction(flat)
        assert nested["sellers"][0]["name"] == NESTED_DATA["sellers"][0]["name"]
        assert nested["buyers"][0]["name"] == NESTED_DATA["buyers"][0]["name"]
        assert nested["property"]["block_number"] == str(NESTED_DATA["property"]["block_number"])
