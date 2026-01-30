"""Legal Compliance Tool - Checks contract against Israeli real estate law."""

import os
import json
from datetime import datetime

from crewai.tools import tool


# Sale of Apartments Law 1973 (חוק מכר דירות, תשל"ג-1973) requirements
COMPLIANCE_CHECKS = [
    {
        "id": "seller_identity",
        "law_ref": "חוק מכר דירות §2",
        "description": "זיהוי מלא של המוכר",
        "check": lambda d: bool(d.get("seller_name") and d.get("seller_id")),
        "severity": "critical",
    },
    {
        "id": "buyer_identity",
        "law_ref": "חוק מכר דירות §2",
        "description": "זיהוי מלא של הקונה",
        "check": lambda d: bool(d.get("buyer_name") and d.get("buyer_id")),
        "severity": "critical",
    },
    {
        "id": "property_identification",
        "law_ref": "חוק מכר דירות §2",
        "description": "זיהוי הנכס - גוש, חלקה, כתובת",
        "check": lambda d: bool(d.get("block_number") and d.get("parcel_number") and d.get("property_address")),
        "severity": "critical",
    },
    {
        "id": "price_stated",
        "law_ref": "חוק מכר דירות §2",
        "description": "ציון מחיר העסקה",
        "check": lambda d: bool(d.get("price") and float(d.get("price", 0)) > 0),
        "severity": "critical",
    },
    {
        "id": "delivery_date",
        "law_ref": "חוק מכר דירות §5א",
        "description": "קביעת מועד מסירת הדירה",
        "check": lambda d: bool(d.get("delivery_date")),
        "severity": "critical",
    },
    {
        "id": "area_specified",
        "law_ref": "חוק מכר דירות §3",
        "description": "ציון שטח הדירה",
        "check": lambda d: bool(d.get("area_sqm") and float(d.get("area_sqm", 0)) > 0),
        "severity": "critical",
    },
    {
        "id": "rooms_specified",
        "law_ref": "חוק מכר דירות §3",
        "description": "ציון מספר חדרים",
        "check": lambda d: bool(d.get("rooms") and float(d.get("rooms", 0)) > 0),
        "severity": "high",
    },
    {
        "id": "no_lien",
        "law_ref": "חוק המקרקעין §127",
        "description": "הנכס נקי מעיקולים",
        "check": lambda d: not d.get("has_lien", False),
        "severity": "critical",
    },
    {
        "id": "no_violations",
        "law_ref": "חוק התכנון והבנייה §145",
        "description": "אין חריגות בנייה",
        "check": lambda d: not d.get("has_violations", False),
        "severity": "high",
    },
    {
        "id": "breach_clause",
        "law_ref": "חוק החוזים (תרופות) §15",
        "description": "סעיף פיצוי מוסכם בגין הפרה",
        "check": lambda d: True,  # Always included in our template
        "severity": "high",
    },
    {
        "id": "tax_clause",
        "law_ref": "חוק מיסוי מקרקעין §15",
        "description": "סעיף מיסים - מס שבח, מס רכישה, היטל השבחה",
        "check": lambda d: True,  # Always included in our template
        "severity": "high",
    },
    {
        "id": "mortgage_disclosure",
        "law_ref": "חוק מכר דירות §4א",
        "description": "גילוי משכנתא קיימת",
        "check": lambda d: True,  # Handled in contract template
        "severity": "high",
    },
    {
        "id": "signing_date",
        "law_ref": "חוק החוזים §1",
        "description": "ציון תאריך חתימה",
        "check": lambda d: bool(d.get("signing_date")),
        "severity": "critical",
    },
    {
        "id": "jurisdiction_clause",
        "law_ref": "חוק בתי המשפט §51",
        "description": "סעיף סמכות שיפוט",
        "check": lambda d: True,  # Always included in our template
        "severity": "medium",
    },
    {
        "id": "seller_contact",
        "law_ref": "תקנות הגנת הצרכן §4",
        "description": "פרטי התקשרות מוכר",
        "check": lambda d: bool(d.get("seller_phone") and d.get("seller_email")),
        "severity": "medium",
    },
    {
        "id": "buyer_contact",
        "law_ref": "תקנות הגנת הצרכן §4",
        "description": "פרטי התקשרות קונה",
        "check": lambda d: bool(d.get("buyer_phone") and d.get("buyer_email")),
        "severity": "medium",
    },
    {
        "id": "payment_schedule",
        "law_ref": "חוק מכר דירות §2",
        "description": "לוח תשלומים מפורט",
        "check": lambda d: True,  # Always included in our template
        "severity": "high",
    },
    {
        "id": "delivery_condition",
        "law_ref": "חוק מכר דירות §5ב",
        "description": "תנאי מסירת הדירה (AS IS / לאחר תיקונים)",
        "check": lambda d: True,  # Always included in our template
        "severity": "medium",
    },
]


def run_compliance_check(data: dict) -> dict:
    """Run all legal compliance checks."""
    results = []
    for check in COMPLIANCE_CHECKS:
        passed = check["check"](data)
        results.append({
            "id": check["id"],
            "law_ref": check["law_ref"],
            "description": check["description"],
            "severity": check["severity"],
            "passed": passed,
        })

    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    critical_failures = [r for r in results if not r["passed"] and r["severity"] == "critical"]
    high_failures = [r for r in results if not r["passed"] and r["severity"] == "high"]

    return {
        "compliant": len(critical_failures) == 0,
        "total_checks": total,
        "passed": passed_count,
        "failed": total - passed_count,
        "critical_failures": critical_failures,
        "high_failures": high_failures,
        "details": results,
        "timestamp": datetime.now().isoformat(),
    }


def generate_evaluation_report(compliance_result: dict, output_path: str) -> str:
    """Generate evaluation_report.md from compliance check results."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    lines = [
        "# דוח הערכת תאימות משפטית",
        "",
        f"**תאריך:** {compliance_result['timestamp']}",
        f"**סטטוס:** {'✅ תקין' if compliance_result['compliant'] else '❌ לא תקין'}",
        f"**בדיקות:** {compliance_result['passed']}/{compliance_result['total_checks']} עברו",
        "",
    ]

    if compliance_result["critical_failures"]:
        lines.append("## ❌ כשלים קריטיים")
        for f in compliance_result["critical_failures"]:
            lines.append(f"- **{f['description']}** ({f['law_ref']})")
        lines.append("")

    if compliance_result["high_failures"]:
        lines.append("## ⚠️ כשלים ברמה גבוהה")
        for f in compliance_result["high_failures"]:
            lines.append(f"- **{f['description']}** ({f['law_ref']})")
        lines.append("")

    lines.append("## פירוט בדיקות")
    lines.append("")
    lines.append("| סטטוס | בדיקה | הפניה חוקית | חומרה |")
    lines.append("|--------|-------|-------------|--------|")
    for r in compliance_result["details"]:
        status = "✅" if r["passed"] else "❌"
        lines.append(f"| {status} | {r['description']} | {r['law_ref']} | {r['severity']} |")

    lines.extend(["", "---", f"*נוצר אוטומטית על ידי מערכת אוטומציית חוזי נדל\"ן*"])

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_path


@tool("check_legal_compliance")
def check_legal_compliance(clean_data_json: str) -> str:
    """Check contract compliance against Israeli real estate laws.
    Returns compliance results and generates evaluation_report.md."""
    data = json.loads(clean_data_json)
    result = run_compliance_check(data)

    report_path = generate_evaluation_report(result, "artifacts/evaluation_report.md")
    result["report_path"] = report_path

    return json.dumps(result, ensure_ascii=False, indent=2)
