"""Crew 1 Tasks - Data Collection and Validation."""

from crewai import Task, Agent


def create_form_generation_task(agent: Agent) -> Task:
    return Task(
        description=(
            "צור טופס HTML לאיסוף נתוני עסקת נדל\"ן. הטופס צריך לכלול:\n"
            "- פרטי מוכר (שם, ת.ז., כתובת, טלפון, דוא\"ל, מצב משפחתי)\n"
            "- פרטי קונה (שם, ת.ז., כתובת, טלפון, דוא\"ל)\n"
            "- פרטי נכס (כתובת, גוש, חלקה, שטח, חדרים, קומה, סוג, חניה, מחסן)\n"
            "- פרטי עסקה (מחיר, תאריך חתימה, תאריך מסירה, הערות)\n"
            "הטופס חייב להיות בעברית עם כיוון RTL."
        ),
        expected_output="נתיב לקובץ HTML של הטופס שנוצר",
        agent=agent,
    )


def create_validation_task(agent: Agent, client_data_json: str) -> Task:
    return Task(
        description=(
            f"אמת את נתוני הלקוח הבאים לפי כל כללי הולידציה (50+ כללים):\n"
            f"{client_data_json}\n\n"
            "בדוק: תעודות זהות ישראליות, טלפונים, דוא\"ל, תאריכים, מספרי גוש וחלקה, "
            "מחירים סבירים, ועוד. צור דוח EDA מפורט בפורמט HTML."
        ),
        expected_output="תוצאות הולידציה בפורמט JSON כולל ציון איכות ורשימת שגיאות",
        agent=agent,
    )


def create_document_processing_task(agent: Agent, client_data_json: str, document_paths: list = None) -> Task:
    doc_info = ""
    if document_paths:
        doc_info = f"\nמסמכים לעיבוד OCR: {', '.join(document_paths)}"

    return Task(
        description=(
            f"עבד את המסמכים הסרוקים וחלץ נתונים מובנים.{doc_info}\n"
            f"נתוני לקוח מהטופס:\n{client_data_json}\n\n"
            "1. אם יש מסמכים סרוקים - בצע OCR וחלץ נתונים\n"
            "2. נקה ומזג את כל הנתונים\n"
            "3. ייצא ל-clean_data.csv, dataset_contract.json, ו-insights.md"
        ),
        expected_output="נתיבים לקבצי הפלט: clean_data.csv, dataset_contract.json, insights.md",
        agent=agent,
    )
