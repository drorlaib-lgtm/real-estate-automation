"""Tests for the complete flow pipeline."""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from crews.crew1_data.tools.validator import run_validation
from crews.crew1_data.tools.data_cleaner import merge_and_clean, generate_dataset_contract
from crews.crew2_contract.tools.contract_builder import build_contract_document
from crews.crew2_contract.tools.legal_compliance import run_compliance_check
from crews.crew2_contract.tools.quality_scorer import calculate_quality_score


SAMPLE_DATA = {
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
    "notes": "הדירה כוללת מזגן",
}


class TestEndToEndPipeline:
    def test_validation_step(self):
        result = run_validation(SAMPLE_DATA)
        assert result["total_rules"] >= 50
        # Most rules should pass with valid sample data
        assert result["passed"] > result["total_rules"] * 0.8

    def test_data_cleaning_step(self):
        clean = merge_and_clean(SAMPLE_DATA)
        assert clean["seller_name"] == "ישראל ישראלי"
        assert clean["seller_id"] == "123456782"
        assert clean["price"] == 2500000.0
        assert clean["area_sqm"] == 95.0
        assert clean["price_per_sqm"] > 0

    def test_dataset_contract_generation(self):
        clean = merge_and_clean(SAMPLE_DATA)
        contract = generate_dataset_contract(clean)
        assert "schema" in contract
        assert "quality_checks" in contract
        assert contract["schema"]["seller_name"]["required"] is True

    def test_contract_building(self):
        clean = merge_and_clean(SAMPLE_DATA)
        doc = build_contract_document(clean, "standard")
        assert doc is not None
        # Check document has content
        assert len(doc.paragraphs) > 10

    def test_contract_mortgage_variation(self):
        clean = merge_and_clean(SAMPLE_DATA)
        doc = build_contract_document(clean, "mortgage")
        assert doc is not None
        assert len(doc.paragraphs) > 10

    def test_compliance_check(self):
        clean = merge_and_clean(SAMPLE_DATA)
        result = run_compliance_check(clean)
        assert result["total_checks"] > 10
        assert result["compliant"] is True  # Sample data should be compliant
        assert len(result["critical_failures"]) == 0

    def test_quality_scoring(self):
        clean = merge_and_clean(SAMPLE_DATA)
        compliance = run_compliance_check(clean)
        quality = calculate_quality_score(clean, compliance)
        assert 0 <= quality["score"] <= 100
        assert quality["grade"] in ["מצוין", "טוב", "בינוני", "חלש"]
        assert quality["recommendation"]

    def test_full_pipeline(self):
        """Test the complete pipeline end-to-end."""
        # Step 1: Validate
        validation = run_validation(SAMPLE_DATA)
        assert validation["passed"] > 0

        # Step 2: Clean
        clean = merge_and_clean(SAMPLE_DATA)
        assert clean["price_per_sqm"] > 0

        # Step 3: Dataset contract
        ds_contract = generate_dataset_contract(clean)
        assert len(ds_contract["schema"]) > 10

        # Step 4: Build contract
        doc = build_contract_document(clean, "standard")
        assert len(doc.paragraphs) > 10

        # Step 5: Compliance
        compliance = run_compliance_check(clean)
        assert compliance["compliant"] is True

        # Step 6: Quality
        quality = calculate_quality_score(clean, compliance)
        assert quality["score"] >= 60  # Good data should score well
