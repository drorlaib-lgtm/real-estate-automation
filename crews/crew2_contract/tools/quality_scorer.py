"""Quality Assurance Tool - Scores contract quality and generates contract card."""

import os
import json
from datetime import datetime

from crewai.tools import tool


def calculate_quality_score(data: dict, compliance_result: dict) -> dict:
    """Calculate a quality score from 0-100 for the contract."""
    score = 100
    deductions = []

    # Data completeness (max -30)
    required_fields = [
        "seller_name", "seller_id", "seller_address", "seller_phone", "seller_email",
        "buyer_name", "buyer_id", "buyer_address", "buyer_phone", "buyer_email",
        "property_address", "block_number", "parcel_number", "area_sqm", "rooms",
        "property_type", "price", "signing_date", "delivery_date",
    ]
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        deduction = min(len(missing) * 3, 30)
        score -= deduction
        deductions.append(f"שדות חסרים ({len(missing)}): -{deduction} נקודות")

    # Legal compliance (max -40)
    critical_count = len(compliance_result.get("critical_failures", []))
    high_count = len(compliance_result.get("high_failures", []))
    if critical_count:
        deduction = min(critical_count * 10, 30)
        score -= deduction
        deductions.append(f"כשלים קריטיים ({critical_count}): -{deduction} נקודות")
    if high_count:
        deduction = min(high_count * 5, 10)
        score -= deduction
        deductions.append(f"כשלים ברמה גבוהה ({high_count}): -{deduction} נקודות")

    # Risk factors (max -20)
    if data.get("has_mortgage"):
        score -= 5
        deductions.append("משכנתא קיימת: -5 נקודות")
    if data.get("has_lien"):
        score -= 10
        deductions.append("עיקול: -10 נקודות")
    if data.get("has_violations"):
        score -= 5
        deductions.append("חריגות בנייה: -5 נקודות")
    if data.get("has_warning_note"):
        score -= 3
        deductions.append("הערת אזהרה: -3 נקודות")

    # Price reasonableness (max -10)
    try:
        ppsm = float(data.get("price", 0)) / max(float(data.get("area_sqm", 1)), 1)
        if ppsm < 5000 or ppsm > 200000:
            score -= 10
            deductions.append(f"מחיר למ\"ר חריג ({ppsm:,.0f}): -10 נקודות")
    except (ValueError, TypeError):
        pass

    score = max(0, min(100, score))

    if score >= 80:
        grade = "מצוין"
        recommendation = "החוזה מוכן לחתימה"
    elif score >= 60:
        grade = "טוב"
        recommendation = "נדרשים תיקונים קלים לפני חתימה"
    elif score >= 40:
        grade = "בינוני"
        recommendation = "נדרשת בדיקה מעמיקה ותיקונים משמעותיים"
    else:
        grade = "חלש"
        recommendation = "החוזה אינו מוכן לחתימה - נדרשת עבודה מחודשת"

    return {
        "score": score,
        "grade": grade,
        "recommendation": recommendation,
        "deductions": deductions,
    }


def generate_contract_card(data: dict, quality: dict, compliance: dict, output_path: str) -> str:
    """Generate contract_card.md summarizing the contract."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    price = float(data.get("price", 0))
    area = float(data.get("area_sqm", 1))

    property_types = {
        "apartment": "דירה", "penthouse": "פנטהאוז", "garden": "דירת גן",
        "duplex": "דופלקס", "house": "בית פרטי", "land": "מגרש",
    }

    lines = [
        "# כרטיס חוזה - Contract Card",
        "",
        "## מטרת החוזה",
        f"חוזה מכר {property_types.get(data.get('property_type', ''), 'נכס')} "
        f"בכתובת {data.get('property_address', 'לא צוין')}.",
        "",
        "## סיכום נתונים",
        f"- **מוכר:** {data.get('seller_name', 'לא צוין')}",
        f"- **קונה:** {data.get('buyer_name', 'לא צוין')}",
        f"- **נכס:** {data.get('property_address', 'לא צוין')}",
        f"- **גוש/חלקה:** {data.get('block_number', '')}/{data.get('parcel_number', '')}",
        f"- **שטח:** {area} מ\"ר | **חדרים:** {data.get('rooms', '')}",
        f"- **מחיר:** {price:,.0f} ₪ | **מחיר למ\"ר:** {price / max(area, 1):,.0f} ₪",
        f"- **תאריך חתימה:** {data.get('signing_date', '')}",
        f"- **תאריך מסירה:** {data.get('delivery_date', '')}",
        "",
        "## ציון איכות",
        f"### {quality['score']}/100 - {quality['grade']}",
        f"**המלצה:** {quality['recommendation']}",
        "",
    ]

    if quality["deductions"]:
        lines.append("## ניכויים")
        for d in quality["deductions"]:
            lines.append(f"- {d}")
        lines.append("")

    lines.extend([
        "## תאימות משפטית",
        f"- בדיקות שעברו: {compliance.get('passed', 0)}/{compliance.get('total_checks', 0)}",
        f"- כשלים קריטיים: {len(compliance.get('critical_failures', []))}",
        f"- כשלים גבוהים: {len(compliance.get('high_failures', []))}",
        "",
        "## מגבלות",
        "- החוזה נוצר אוטומטית ודורש בדיקה של עורך דין",
        "- ייתכנו סעיפים שדורשים התאמה למקרה הספציפי",
        "- OCR על מסמכים סרוקים עלול להכיל שגיאות",
        "- יש לוודא פרטים מול נסח טאבו עדכני",
        "",
        "## שיקולים אתיים",
        "- המערכת אינה מחליפה ייעוץ משפטי מקצועי",
        "- יש לוודא שכל הצדדים מבינים את תנאי החוזה",
        "- הנתונים מטופלים בסודיות ובהתאם לחוק הגנת הפרטיות",
        "",
        "---",
        f"*נוצר: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
    ])

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_path


@tool("score_contract_quality")
def score_contract_quality(clean_data_json: str, compliance_json: str) -> str:
    """Score contract quality 0-100 and generate contract_card.md.
    Returns quality assessment as JSON."""
    data = json.loads(clean_data_json)
    compliance = json.loads(compliance_json)

    quality = calculate_quality_score(data, compliance)
    card_path = generate_contract_card(data, quality, compliance, "artifacts/contract_card.md")
    quality["contract_card_path"] = card_path

    return json.dumps(quality, ensure_ascii=False, indent=2)
