"""Data Validator Tool - Validates client and property data with 50+ rules."""

import re
import json
import os
from datetime import datetime, date
from typing import Any

import pandas as pd
from crewai.tools import tool


def validate_israeli_id(id_number: str) -> bool:
    """Validate Israeli ID number using the Luhn-like algorithm."""
    id_str = id_number.strip()
    if not id_str or not id_str.isdigit():
        return False
    id_str = id_str.zfill(9)
    if len(id_str) != 9:
        return False
    total = 0
    for i, digit in enumerate(id_str):
        val = int(digit) * ((i % 2) + 1)
        if val > 9:
            val -= 9
        total += val
    return total % 10 == 0


def validate_israeli_phone(phone: str) -> bool:
    """Validate Israeli phone number."""
    cleaned = re.sub(r"[\s\-\(\)]", "", phone)
    return bool(re.match(r"^0[2-9]\d{7,8}$", cleaned))


def validate_email(email: str) -> bool:
    """Validate email address format."""
    return bool(re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", email))


def validate_date(date_str: str) -> bool:
    """Validate date string in YYYY-MM-DD format."""
    try:
        datetime.strptime(str(date_str), "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def validate_block_number(block: str) -> bool:
    """Validate land registry block number."""
    return bool(re.match(r"^\d{1,6}$", str(block).strip()))


def validate_parcel_number(parcel: str) -> bool:
    """Validate land registry parcel number."""
    return bool(re.match(r"^\d{1,5}$", str(parcel).strip()))


def validate_price(price: Any) -> bool:
    """Validate transaction price is reasonable."""
    try:
        p = float(price)
        return 50000 <= p <= 100000000
    except (ValueError, TypeError):
        return False


def validate_area(area: Any) -> bool:
    """Validate property area in sqm."""
    try:
        a = float(area)
        return 10 <= a <= 5000
    except (ValueError, TypeError):
        return False


def validate_rooms(rooms: Any) -> bool:
    """Validate number of rooms."""
    try:
        r = float(rooms)
        return 1 <= r <= 20
    except (ValueError, TypeError):
        return False


def validate_hebrew_name(name: str) -> bool:
    """Validate Hebrew name contains Hebrew characters."""
    return bool(re.search(r"[\u0590-\u05FF]", str(name)))


def validate_delivery_after_signing(signing: str, delivery: str) -> bool:
    """Validate delivery date is after signing date."""
    try:
        s = datetime.strptime(str(signing), "%Y-%m-%d")
        d = datetime.strptime(str(delivery), "%Y-%m-%d")
        return d >= s
    except (ValueError, TypeError):
        return False


# All validation rules
VALIDATION_RULES = {
    # Seller validations
    "seller_name_required": {"field": "seller_name", "check": lambda v: bool(v and str(v).strip()), "msg": "שם המוכר חסר"},
    "seller_name_hebrew": {"field": "seller_name", "check": validate_hebrew_name, "msg": "שם המוכר חייב להכיל אותיות בעברית"},
    "seller_name_length": {"field": "seller_name", "check": lambda v: 2 <= len(str(v).strip()) <= 100, "msg": "שם המוכר חייב להיות בין 2 ל-100 תווים"},
    "seller_id_required": {"field": "seller_id", "check": lambda v: bool(v and str(v).strip()), "msg": "תעודת זהות מוכר חסרה"},
    "seller_id_valid": {"field": "seller_id", "check": validate_israeli_id, "msg": "תעודת זהות מוכר לא תקינה"},
    "seller_address_required": {"field": "seller_address", "check": lambda v: bool(v and str(v).strip()), "msg": "כתובת מוכר חסרה"},
    "seller_address_length": {"field": "seller_address", "check": lambda v: len(str(v).strip()) >= 5, "msg": "כתובת מוכר קצרה מדי"},
    "seller_phone_required": {"field": "seller_phone", "check": lambda v: bool(v and str(v).strip()), "msg": "טלפון מוכר חסר"},
    "seller_phone_valid": {"field": "seller_phone", "check": validate_israeli_phone, "msg": "טלפון מוכר לא תקין"},
    "seller_email_required": {"field": "seller_email", "check": lambda v: bool(v and str(v).strip()), "msg": "דוא\"ל מוכר חסר"},
    "seller_email_valid": {"field": "seller_email", "check": validate_email, "msg": "דוא\"ל מוכר לא תקין"},
    # Buyer validations
    "buyer_name_required": {"field": "buyer_name", "check": lambda v: bool(v and str(v).strip()), "msg": "שם הקונה חסר"},
    "buyer_name_hebrew": {"field": "buyer_name", "check": validate_hebrew_name, "msg": "שם הקונה חייב להכיל אותיות בעברית"},
    "buyer_name_length": {"field": "buyer_name", "check": lambda v: 2 <= len(str(v).strip()) <= 100, "msg": "שם הקונה חייב להיות בין 2 ל-100 תווים"},
    "buyer_id_required": {"field": "buyer_id", "check": lambda v: bool(v and str(v).strip()), "msg": "תעודת זהות קונה חסרה"},
    "buyer_id_valid": {"field": "buyer_id", "check": validate_israeli_id, "msg": "תעודת זהות קונה לא תקינה"},
    "buyer_address_required": {"field": "buyer_address", "check": lambda v: bool(v and str(v).strip()), "msg": "כתובת קונה חסרה"},
    "buyer_address_length": {"field": "buyer_address", "check": lambda v: len(str(v).strip()) >= 5, "msg": "כתובת קונה קצרה מדי"},
    "buyer_phone_required": {"field": "buyer_phone", "check": lambda v: bool(v and str(v).strip()), "msg": "טלפון קונה חסר"},
    "buyer_phone_valid": {"field": "buyer_phone", "check": validate_israeli_phone, "msg": "טלפון קונה לא תקין"},
    "buyer_email_required": {"field": "buyer_email", "check": lambda v: bool(v and str(v).strip()), "msg": "דוא\"ל קונה חסר"},
    "buyer_email_valid": {"field": "buyer_email", "check": validate_email, "msg": "דוא\"ל קונה לא תקין"},
    # Property validations
    "property_address_required": {"field": "property_address", "check": lambda v: bool(v and str(v).strip()), "msg": "כתובת נכס חסרה"},
    "property_address_length": {"field": "property_address", "check": lambda v: len(str(v).strip()) >= 5, "msg": "כתובת נכס קצרה מדי"},
    "block_required": {"field": "block_number", "check": lambda v: bool(v and str(v).strip()), "msg": "מספר גוש חסר"},
    "block_valid": {"field": "block_number", "check": validate_block_number, "msg": "מספר גוש לא תקין"},
    "parcel_required": {"field": "parcel_number", "check": lambda v: bool(v and str(v).strip()), "msg": "מספר חלקה חסר"},
    "parcel_valid": {"field": "parcel_number", "check": validate_parcel_number, "msg": "מספר חלקה לא תקין"},
    "area_required": {"field": "area_sqm", "check": lambda v: v is not None and str(v).strip() != "", "msg": "שטח הנכס חסר"},
    "area_valid": {"field": "area_sqm", "check": validate_area, "msg": "שטח הנכס לא סביר (10-5000 מ\"ר)"},
    "rooms_required": {"field": "rooms", "check": lambda v: v is not None and str(v).strip() != "", "msg": "מספר חדרים חסר"},
    "rooms_valid": {"field": "rooms", "check": validate_rooms, "msg": "מספר חדרים לא סביר (1-20)"},
    "property_type_required": {"field": "property_type", "check": lambda v: v in ("apartment", "penthouse", "garden", "duplex", "house", "land"), "msg": "סוג נכס לא תקין"},
    # Transaction validations
    "price_required": {"field": "price", "check": lambda v: v is not None and str(v).strip() != "", "msg": "מחיר העסקה חסר"},
    "price_valid": {"field": "price", "check": validate_price, "msg": "מחיר לא סביר (50,000-100,000,000 ₪)"},
    "signing_date_required": {"field": "signing_date", "check": lambda v: bool(v and str(v).strip()), "msg": "תאריך חתימה חסר"},
    "signing_date_valid": {"field": "signing_date", "check": validate_date, "msg": "תאריך חתימה לא תקין"},
    "delivery_date_required": {"field": "delivery_date", "check": lambda v: bool(v and str(v).strip()), "msg": "תאריך מסירה חסר"},
    "delivery_date_valid": {"field": "delivery_date", "check": validate_date, "msg": "תאריך מסירה לא תקין"},
    # Cross-field validations
    "different_parties": {"field": "seller_id", "check": None, "msg": "תעודת זהות מוכר וקונה זהות", "cross": True},
    "delivery_after_signing": {"field": "signing_date", "check": None, "msg": "תאריך מסירה חייב להיות אחרי תאריך חתימה", "cross": True},
    # Additional validations
    "seller_marital_valid": {"field": "seller_marital_status", "check": lambda v: not v or v in ("single", "married", "divorced", "widowed", ""), "msg": "מצב משפחתי מוכר לא תקין"},
    "parking_valid": {"field": "parking", "check": lambda v: not v or v in ("none", "covered", "uncovered", "underground", ""), "msg": "סוג חניה לא תקין"},
    "storage_valid": {"field": "storage", "check": lambda v: not v or v in ("yes", "no", ""), "msg": "שדה מחסן לא תקין"},
    "floor_valid": {"field": "floor", "check": lambda v: not v or -5 <= int(v) <= 100, "msg": "קומה לא סבירה"},
    "price_per_sqm_reasonable": {"field": "price", "check": None, "msg": "מחיר למ\"ר לא סביר", "cross": True},
    "future_signing_date": {"field": "signing_date", "check": lambda v: not v or datetime.strptime(str(v), "%Y-%m-%d").date() >= date.today(), "msg": "תאריך חתימה חייב להיות בעתיד"},
    "notes_length": {"field": "notes", "check": lambda v: not v or len(str(v)) <= 5000, "msg": "הערות ארוכות מדי (מקסימום 5000 תווים)"},
    "sub_parcel_valid": {"field": "sub_parcel", "check": lambda v: not v or re.match(r"^\d{1,4}$", str(v).strip()), "msg": "תת-חלקה לא תקינה"},
    "seller_name_not_buyer_name": {"field": "seller_name", "check": None, "msg": "שם המוכר זהה לשם הקונה", "cross": True},
}


def run_validation(data: dict) -> dict:
    """Run all validation rules on the data. Returns dict with errors and warnings."""
    errors = []
    warnings = []
    passed = []

    for rule_name, rule in VALIDATION_RULES.items():
        field = rule["field"]
        value = data.get(field, "")

        if rule.get("cross"):
            if rule_name == "different_parties":
                if data.get("seller_id") and data.get("buyer_id") and data["seller_id"] == data["buyer_id"]:
                    errors.append({"rule": rule_name, "field": field, "message": rule["msg"]})
                else:
                    passed.append(rule_name)
            elif rule_name == "delivery_after_signing":
                s, d = data.get("signing_date"), data.get("delivery_date")
                if s and d and not validate_delivery_after_signing(s, d):
                    errors.append({"rule": rule_name, "field": field, "message": rule["msg"]})
                else:
                    passed.append(rule_name)
            elif rule_name == "seller_name_not_buyer_name":
                if data.get("seller_name") and data.get("buyer_name") and data["seller_name"] == data["buyer_name"]:
                    warnings.append({"rule": rule_name, "field": field, "message": rule["msg"]})
                else:
                    passed.append(rule_name)
            elif rule_name == "price_per_sqm_reasonable":
                try:
                    price = float(data.get("price", 0))
                    area = float(data.get("area_sqm", 1))
                    ppsm = price / area
                    if ppsm < 5000 or ppsm > 200000:
                        warnings.append({"rule": rule_name, "field": field, "message": rule["msg"]})
                    else:
                        passed.append(rule_name)
                except (ValueError, TypeError, ZeroDivisionError):
                    passed.append(rule_name)
            continue

        try:
            if rule["check"] and not rule["check"](value):
                errors.append({"rule": rule_name, "field": field, "message": rule["msg"]})
            else:
                passed.append(rule_name)
        except Exception:
            errors.append({"rule": rule_name, "field": field, "message": rule["msg"]})

    return {
        "valid": len(errors) == 0,
        "total_rules": len(VALIDATION_RULES),
        "passed": len(passed),
        "errors": errors,
        "warnings": warnings,
    }


def generate_eda_report(data: dict, validation_result: dict, output_path: str) -> str:
    """Generate an EDA HTML report from the validated data."""
    errors_html = ""
    for err in validation_result["errors"]:
        errors_html += f'<tr><td>{err["rule"]}</td><td>{err["field"]}</td><td class="error">{err["message"]}</td></tr>\n'

    warnings_html = ""
    for warn in validation_result["warnings"]:
        warnings_html += f'<tr><td>{warn["rule"]}</td><td>{warn["field"]}</td><td class="warning">{warn["message"]}</td></tr>\n'

    fields_html = ""
    for key, val in data.items():
        status = "✅" if not any(e["field"] == key for e in validation_result["errors"]) else "❌"
        fields_html += f"<tr><td>{status}</td><td>{key}</td><td>{val}</td></tr>\n"

    score = round(validation_result["passed"] / max(validation_result["total_rules"], 1) * 100, 1)

    html = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>דוח ניתוח נתונים - EDA Report</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; direction: rtl; padding: 20px; background: #f0f0f0; }}
        .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }}
        h1 {{ color: #1a237e; text-align: center; }}
        h2 {{ color: #283593; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: right; }}
        th {{ background: #3f51b5; color: white; }}
        .error {{ color: #d32f2f; font-weight: bold; }}
        .warning {{ color: #f57c00; }}
        .score {{ font-size: 48px; text-align: center; color: {"#4caf50" if score >= 80 else "#f57c00" if score >= 50 else "#d32f2f"}; }}
        .summary {{ background: #e8eaf6; padding: 15px; border-radius: 4px; margin: 15px 0; }}
    </style>
</head>
<body>
<div class="container">
    <h1>📊 דוח ניתוח נתונים (EDA)</h1>
    <div class="summary">
        <p class="score">{score}%</p>
        <p style="text-align:center;">ציון איכות נתונים</p>
        <p>סה"כ כללים: {validation_result["total_rules"]} | עברו: {validation_result["passed"]} | שגיאות: {len(validation_result["errors"])} | אזהרות: {len(validation_result["warnings"])}</p>
    </div>

    <h2>סקירת שדות</h2>
    <table>
        <tr><th>סטטוס</th><th>שדה</th><th>ערך</th></tr>
        {fields_html}
    </table>

    {"<h2>שגיאות</h2><table><tr><th>כלל</th><th>שדה</th><th>הודעה</th></tr>" + errors_html + "</table>" if errors_html else ""}
    {"<h2>אזהרות</h2><table><tr><th>כלל</th><th>שדה</th><th>הודעה</th></tr>" + warnings_html + "</table>" if warnings_html else ""}

    <p style="text-align:center; color:#999; margin-top:30px;">נוצר אוטומטית על ידי מערכת אוטומציית חוזי נדל"ן | {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
</div>
</body>
</html>"""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path


@tool("validate_client_data")
def validate_client_data(data_json: str) -> str:
    """Validate client and property data against 50+ rules.
    Input: JSON string of client data.
    Returns: validation results as JSON string."""
    data = json.loads(data_json)
    result = run_validation(data)

    eda_path = generate_eda_report(data, result, "artifacts/eda_report.html")
    result["eda_report_path"] = eda_path

    return json.dumps(result, ensure_ascii=False, indent=2)
