"""Data Cleaner Tool - Cleans and merges data into clean_data.csv and dataset_contract.json."""

import os
import json
import re
from datetime import datetime

import pandas as pd
from crewai.tools import tool


def clean_phone(phone: str) -> str:
    """Normalize phone number format."""
    if not phone:
        return ""
    cleaned = re.sub(r"[\s\-\(\)\+]", "", str(phone))
    if cleaned.startswith("972"):
        cleaned = "0" + cleaned[3:]
    return cleaned


def clean_id(id_num: str) -> str:
    """Normalize ID number to 9 digits."""
    if not id_num:
        return ""
    return str(id_num).strip().zfill(9)


def clean_name(name: str) -> str:
    """Clean and normalize name."""
    if not name:
        return ""
    return " ".join(str(name).strip().split())


def clean_price(price) -> float:
    """Clean price value."""
    if not price:
        return 0.0
    cleaned = re.sub(r"[^\d.]", "", str(price))
    return float(cleaned) if cleaned else 0.0


def merge_and_clean(client_data: dict, ocr_data: dict = None) -> dict:
    """Merge client form data with OCR extracted data and clean all fields."""
    merged = {}

    # Clean client data
    merged["seller_name"] = clean_name(client_data.get("seller_name", ""))
    merged["seller_id"] = clean_id(client_data.get("seller_id", ""))
    merged["seller_address"] = str(client_data.get("seller_address", "")).strip()
    merged["seller_phone"] = clean_phone(client_data.get("seller_phone", ""))
    merged["seller_email"] = str(client_data.get("seller_email", "")).strip().lower()
    merged["seller_marital_status"] = str(client_data.get("seller_marital_status", "")).strip()

    merged["buyer_name"] = clean_name(client_data.get("buyer_name", ""))
    merged["buyer_id"] = clean_id(client_data.get("buyer_id", ""))
    merged["buyer_address"] = str(client_data.get("buyer_address", "")).strip()
    merged["buyer_phone"] = clean_phone(client_data.get("buyer_phone", ""))
    merged["buyer_email"] = str(client_data.get("buyer_email", "")).strip().lower()

    merged["property_address"] = str(client_data.get("property_address", "")).strip()
    merged["property_type"] = str(client_data.get("property_type", "")).strip()
    merged["parking"] = str(client_data.get("parking", "none")).strip()
    merged["storage"] = str(client_data.get("storage", "no")).strip()
    merged["notes"] = str(client_data.get("notes", "")).strip()

    # Prefer OCR data for land registry fields, fallback to form data
    if ocr_data:
        merged["block_number"] = str(ocr_data.get("block_number", client_data.get("block_number", ""))).strip()
        merged["parcel_number"] = str(ocr_data.get("parcel_number", client_data.get("parcel_number", ""))).strip()
        merged["sub_parcel"] = str(ocr_data.get("sub_parcel", client_data.get("sub_parcel", ""))).strip()
        merged["area_sqm"] = float(ocr_data.get("area_sqm", client_data.get("area_sqm", 0)))
        merged["registered_owner"] = ocr_data.get("registered_owner", "")
        merged["has_mortgage"] = ocr_data.get("has_mortgage", False)
        merged["has_lien"] = ocr_data.get("has_lien", False)
        merged["has_warning_note"] = ocr_data.get("has_warning_note", False)
        merged["rights_type"] = ocr_data.get("rights_type", "")
        merged["zoning"] = ocr_data.get("zoning", "")
        merged["has_violations"] = ocr_data.get("has_violations", False)
    else:
        merged["block_number"] = str(client_data.get("block_number", "")).strip()
        merged["parcel_number"] = str(client_data.get("parcel_number", "")).strip()
        merged["sub_parcel"] = str(client_data.get("sub_parcel", "")).strip()
        merged["area_sqm"] = float(client_data.get("area_sqm", 0))
        merged["registered_owner"] = ""
        merged["has_mortgage"] = False
        merged["has_lien"] = False
        merged["has_warning_note"] = False
        merged["rights_type"] = ""
        merged["zoning"] = ""
        merged["has_violations"] = False

    merged["rooms"] = float(client_data.get("rooms", 0))
    merged["floor"] = int(client_data.get("floor", 0)) if client_data.get("floor") else 0
    merged["price"] = clean_price(client_data.get("price", 0))
    merged["signing_date"] = str(client_data.get("signing_date", "")).strip()
    merged["delivery_date"] = str(client_data.get("delivery_date", "")).strip()

    # Computed fields
    if merged["area_sqm"] > 0:
        merged["price_per_sqm"] = round(merged["price"] / merged["area_sqm"], 2)
    else:
        merged["price_per_sqm"] = 0

    merged["processed_at"] = datetime.now().isoformat()

    return merged


def generate_dataset_contract(clean_data: dict) -> dict:
    """Generate a dataset contract JSON defining the schema and constraints."""
    return {
        "version": "1.0",
        "generated_at": datetime.now().isoformat(),
        "description": "Dataset contract for real estate transaction data",
        "schema": {
            "seller_name": {"type": "string", "required": True, "min_length": 2},
            "seller_id": {"type": "string", "required": True, "pattern": r"^\d{9}$"},
            "seller_address": {"type": "string", "required": True},
            "seller_phone": {"type": "string", "required": True, "pattern": r"^0\d{8,9}$"},
            "seller_email": {"type": "string", "required": True, "format": "email"},
            "buyer_name": {"type": "string", "required": True, "min_length": 2},
            "buyer_id": {"type": "string", "required": True, "pattern": r"^\d{9}$"},
            "buyer_address": {"type": "string", "required": True},
            "buyer_phone": {"type": "string", "required": True, "pattern": r"^0\d{8,9}$"},
            "buyer_email": {"type": "string", "required": True, "format": "email"},
            "property_address": {"type": "string", "required": True},
            "block_number": {"type": "string", "required": True},
            "parcel_number": {"type": "string", "required": True},
            "sub_parcel": {"type": "string", "required": False},
            "area_sqm": {"type": "number", "required": True, "min": 10, "max": 5000},
            "rooms": {"type": "number", "required": True, "min": 1, "max": 20},
            "floor": {"type": "integer", "required": False},
            "property_type": {"type": "string", "required": True, "enum": ["apartment", "penthouse", "garden", "duplex", "house", "land"]},
            "price": {"type": "number", "required": True, "min": 50000},
            "signing_date": {"type": "string", "required": True, "format": "date"},
            "delivery_date": {"type": "string", "required": True, "format": "date"},
        },
        "quality_checks": [
            "seller_id != buyer_id",
            "delivery_date >= signing_date",
            "price_per_sqm between 5000 and 200000",
            "has_lien == False (warning if True)",
            "has_violations == False (warning if True)",
        ],
        "data_summary": {
            "total_fields": len(clean_data),
            "filled_fields": sum(1 for v in clean_data.values() if v not in (None, "", 0, False)),
        },
    }


@tool("clean_and_export_data")
def clean_and_export_data(client_data_json: str, ocr_data_json: str = "{}") -> str:
    """Clean, merge client and OCR data, export to clean_data.csv and dataset_contract.json.
    Returns paths to generated files."""
    client_data = json.loads(client_data_json)
    ocr_data = json.loads(ocr_data_json) if ocr_data_json else {}

    clean_data = merge_and_clean(client_data, ocr_data)

    os.makedirs("artifacts", exist_ok=True)

    # Save clean_data.csv
    df = pd.DataFrame([clean_data])
    csv_path = "artifacts/clean_data.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    # Save dataset_contract.json
    contract = generate_dataset_contract(clean_data)
    contract_path = "artifacts/dataset_contract.json"
    with open(contract_path, "w", encoding="utf-8") as f:
        json.dump(contract, f, ensure_ascii=False, indent=2)

    # Save insights.md
    insights_path = "artifacts/insights.md"
    with open(insights_path, "w", encoding="utf-8") as f:
        f.write("# תובנות עסקיות - סיכום נתונים\n\n")
        f.write(f"## פרטי העסקה\n")
        f.write(f"- **מוכר:** {clean_data['seller_name']} (ת.ז. {clean_data['seller_id']})\n")
        f.write(f"- **קונה:** {clean_data['buyer_name']} (ת.ז. {clean_data['buyer_id']})\n")
        f.write(f"- **נכס:** {clean_data['property_address']}\n")
        f.write(f"- **גוש/חלקה:** {clean_data['block_number']}/{clean_data['parcel_number']}\n")
        f.write(f"- **שטח:** {clean_data['area_sqm']} מ\"ר\n")
        f.write(f"- **חדרים:** {clean_data['rooms']}\n")
        f.write(f"- **מחיר:** {clean_data['price']:,.0f} ₪\n")
        f.write(f"- **מחיר למ\"ר:** {clean_data['price_per_sqm']:,.0f} ₪\n\n")
        f.write(f"## סטטוס משפטי\n")
        f.write(f"- משכנתא: {'כן' if clean_data.get('has_mortgage') else 'לא'}\n")
        f.write(f"- עיקול: {'כן' if clean_data.get('has_lien') else 'לא'}\n")
        f.write(f"- הערת אזהרה: {'כן' if clean_data.get('has_warning_note') else 'לא'}\n")
        f.write(f"- חריגות בנייה: {'כן' if clean_data.get('has_violations') else 'לא'}\n\n")
        f.write(f"## לוח זמנים\n")
        f.write(f"- תאריך חתימה: {clean_data['signing_date']}\n")
        f.write(f"- תאריך מסירה: {clean_data['delivery_date']}\n\n")
        f.write(f"---\n*נוצר אוטומטית: {clean_data['processed_at']}*\n")

    return json.dumps({
        "clean_data_path": csv_path,
        "dataset_contract_path": contract_path,
        "insights_path": insights_path,
        "total_fields": len(clean_data),
    }, ensure_ascii=False)
