"""Contract Builder Tool - Generates Hebrew legal contracts as DOCX."""

import os
import json
from datetime import datetime

from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from crewai.tools import tool


def number_to_hebrew_words(n: int) -> str:
    """Convert number to Hebrew words (simplified)."""
    units = ["", "אחד", "שניים", "שלושה", "ארבעה", "חמישה", "שישה", "שבעה", "שמונה", "תשעה"]
    tens = ["", "עשר", "עשרים", "שלושים", "ארבעים", "חמישים", "שישים", "שבעים", "שמונים", "תשעים"]
    if n < 10:
        return units[n]
    if n < 100:
        t, u = divmod(n, 10)
        return f"{tens[t]} ו{units[u]}" if u else tens[t]
    return str(n)


def format_price_hebrew(price: float) -> str:
    """Format price with Hebrew notation."""
    return f"{price:,.0f} ₪ ({number_to_hebrew_words(int(price // 1000000))} מיליון ש\"ח)" if price >= 1000000 else f"{price:,.0f} ₪"


def build_contract_document(data: dict, variation: str = "standard") -> Document:
    """Build a complete Hebrew real estate contract as a DOCX document."""
    doc = Document()

    # Set default RTL style
    style = doc.styles["Normal"]
    style.font.name = "David"
    style.font.size = Pt(12)

    # Title
    title = doc.add_heading("חוזה מכר דירה", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph(f'נערך ונחתם ביום {data.get("signing_date", "_________")}')
    doc.add_paragraph("")

    # Parties
    doc.add_heading("בין הצדדים:", level=1)
    doc.add_paragraph(
        f'שם: {data.get("seller_name", "_________")}\n'
        f'ת.ז.: {data.get("seller_id", "_________")}\n'
        f'כתובת: {data.get("seller_address", "_________")}\n'
        f'טלפון: {data.get("seller_phone", "_________")}\n'
        f'דוא"ל: {data.get("seller_email", "_________")}\n'
        f'(להלן: "המוכר")'
    )
    doc.add_paragraph("לבין:")
    doc.add_paragraph(
        f'שם: {data.get("buyer_name", "_________")}\n'
        f'ת.ז.: {data.get("buyer_id", "_________")}\n'
        f'כתובת: {data.get("buyer_address", "_________")}\n'
        f'טלפון: {data.get("buyer_phone", "_________")}\n'
        f'דוא"ל: {data.get("buyer_email", "_________")}\n'
        f'(להלן: "הקונה")'
    )

    # Preamble
    doc.add_heading("הואיל:", level=1)
    doc.add_paragraph(
        f'והמוכר הינו הבעלים הרשום של דירה בכתובת {data.get("property_address", "_________")}, '
        f'הידועה כגוש {data.get("block_number", "_____")} '
        f'חלקה {data.get("parcel_number", "_____")} '
        f'{"תת-חלקה " + str(data.get("sub_parcel", "")) if data.get("sub_parcel") else ""} '
        f'בשטח של {data.get("area_sqm", "_____")} מ"ר (להלן: "הדירה");'
    )
    doc.add_paragraph("והמוכר מעוניין למכור את הדירה והקונה מעוניין לרכוש אותה;")
    doc.add_paragraph("לפיכך הוסכם, הותנה והוצהר בין הצדדים כדלקמן:")

    # Section 1: Declarations
    doc.add_heading("1. הצהרות המוכר", level=1)
    declarations = [
        "המוכר מצהיר כי הוא הבעלים הבלעדי והחוקי של הדירה.",
        "הדירה נקייה מכל שעבוד, עיקול, משכנתא או זכות צד שלישי כלשהי." if not data.get("has_mortgage") else "על הדירה רשומה משכנתא אשר תוסר עד למועד המסירה.",
        "לא קיימות חריגות בנייה בדירה." if not data.get("has_violations") else "קיימות חריגות בנייה כמפורט בנספח.",
        "המוכר מתחייב למסור את הדירה כשהיא פנויה מכל אדם וחפץ.",
        f'הדירה כוללת {data.get("rooms", "_")} חדרים, בקומה {data.get("floor", "_")}.',
    ]
    if data.get("parking") and data["parking"] != "none":
        parking_types = {"covered": "מקורה", "uncovered": "לא מקורה", "underground": "תת-קרקעית"}
        declarations.append(f'הדירה כוללת חניה {parking_types.get(data["parking"], data["parking"])}.')
    if data.get("storage") == "yes":
        declarations.append("הדירה כוללת מחסן.")

    for i, decl in enumerate(declarations, 1):
        doc.add_paragraph(f"1.{i} {decl}")

    # Section 2: Price
    price = data.get("price", 0)
    doc.add_heading("2. התמורה", level=1)
    doc.add_paragraph(f"2.1 מחיר הדירה הוסכם על סך של {format_price_hebrew(price)}.")

    if variation == "standard":
        doc.add_paragraph("2.2 התמורה תשולם בתשלומים כדלקמן:")
        doc.add_paragraph(f"   א. במעמד החתימה: {format_price_hebrew(price * 0.10)} (10%)")
        doc.add_paragraph(f"   ב. תוך 30 יום: {format_price_hebrew(price * 0.30)} (30%)")
        doc.add_paragraph(f"   ג. במעמד המסירה: {format_price_hebrew(price * 0.60)} (60%)")
    elif variation == "mortgage":
        doc.add_paragraph("2.2 התמורה תשולם בתשלומים כדלקמן:")
        doc.add_paragraph(f"   א. במעמד החתימה: {format_price_hebrew(price * 0.10)} (10%)")
        doc.add_paragraph(f"   ב. תוך 30 יום: {format_price_hebrew(price * 0.15)} (15%)")
        doc.add_paragraph(f"   ג. ממשכנתא: {format_price_hebrew(price * 0.50)} (50%)")
        doc.add_paragraph(f"   ד. במעמד המסירה: {format_price_hebrew(price * 0.25)} (25%)")

    # Section 3: Delivery
    doc.add_heading("3. מסירת החזקה", level=1)
    doc.add_paragraph(f'3.1 המוכר מתחייב למסור את החזקה בדירה לקונה ביום {data.get("delivery_date", "_________")}.')
    doc.add_paragraph("3.2 הדירה תימסר כשהיא פנויה מכל אדם וחפץ, במצבה כפי שהיא (AS IS).")
    doc.add_paragraph("3.3 איחור של עד 14 יום במסירה לא ייחשב כהפרה.")

    # Section 4: Taxes
    doc.add_heading("4. מיסים", level=1)
    doc.add_paragraph("4.1 מס שבח - ישולם על ידי המוכר.")
    doc.add_paragraph("4.2 מס רכישה - ישולם על ידי הקונה.")
    doc.add_paragraph("4.3 היטל השבחה - ישולם על ידי המוכר.")
    doc.add_paragraph("4.4 כל מס או היטל אחר יחול על הצד שהחוק מטיל עליו.")

    # Section 5: Breach
    doc.add_heading("5. הפרות וסעדים", level=1)
    doc.add_paragraph("5.1 הפרה יסודית של חוזה זה תזכה את הצד הנפגע בפיצוי מוסכם בסך 10% ממחיר העסקה.")
    doc.add_paragraph(f"5.2 סכום הפיצוי המוסכם: {format_price_hebrew(price * 0.10)}.")
    doc.add_paragraph("5.3 אין בפיצוי המוסכם כדי לגרוע מזכות הצד הנפגע לתבוע פיצויים בגין נזקים בפועל.")

    # Section 6: General
    doc.add_heading("6. כללי", level=1)
    doc.add_paragraph("6.1 חוזה זה מהווה את ההסכם המלא בין הצדדים ומבטל כל הסכם או הבנה קודמים.")
    doc.add_paragraph("6.2 כל שינוי בחוזה זה יעשה בכתב ובחתימת שני הצדדים.")
    doc.add_paragraph("6.3 סמכות השיפוט הבלעדית נתונה לבתי המשפט במחוז בו נמצאת הדירה.")
    doc.add_paragraph("6.4 חוזה זה נערך בשני עותקים, עותק אחד לכל צד.")

    if data.get("notes"):
        doc.add_heading("7. הערות נוספות", level=1)
        doc.add_paragraph(data["notes"])

    # Signatures
    doc.add_paragraph("")
    doc.add_paragraph("ולראיה באו הצדדים על החתום:")
    doc.add_paragraph("")
    table = doc.add_table(rows=3, cols=2)
    table.cell(0, 0).text = "המוכר"
    table.cell(0, 1).text = "הקונה"
    table.cell(1, 0).text = f'שם: {data.get("seller_name", "_________")}'
    table.cell(1, 1).text = f'שם: {data.get("buyer_name", "_________")}'
    table.cell(2, 0).text = "חתימה: _________"
    table.cell(2, 1).text = "חתימה: _________"

    return doc


@tool("build_contract")
def build_contract(clean_data_json: str, variation: str = "standard") -> str:
    """Build a complete Hebrew real estate contract in DOCX format.
    variation: 'standard' or 'mortgage' for different payment schedules.
    Returns path to the generated contract file."""
    data = json.loads(clean_data_json)
    doc = build_contract_document(data, variation)

    os.makedirs("artifacts", exist_ok=True)
    filename = f"artifacts/contract_{variation}.docx"
    doc.save(filename)
    return f"חוזה נוצר בהצלחה: {filename}"
