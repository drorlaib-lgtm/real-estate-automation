"""Crew 1 Agents - Data Collection and Validation Team."""

from crewai import Agent

from crews.crew1_data.tools.form_generator import generate_client_form
from crews.crew1_data.tools.validator import validate_client_data
from crews.crew1_data.tools.ocr_processor import process_document_ocr
from crews.crew1_data.tools.data_cleaner import clean_and_export_data


def create_form_generator_agent() -> Agent:
    return Agent(
        role="מחולל טפסים",
        goal="ליצור טפסי HTML לאיסוף נתוני לקוחות בעסקאות נדל\"ן, בעברית ובכיוון RTL",
        backstory=(
            "אתה מומחה ביצירת טפסים דיגיטליים לאיסוף מידע מלקוחות בתחום הנדל\"ן. "
            "אתה יודע אילו שדות נדרשים לעסקת מכר דירה בישראל ומייצר טפסים ברורים ונוחים בעברית."
        ),
        tools=[generate_client_form],
        verbose=True,
    )


def create_data_validator_agent() -> Agent:
    return Agent(
        role="מאמת נתונים",
        goal="לאמת את הנתונים שהתקבלו מהלקוח לפי 50+ כללי ולידציה, כולל בדיקת תעודת זהות ישראלית",
        backstory=(
            "אתה מומחה באיכות נתונים ובדיקות תקינות. אתה מכיר את כל הכללים הנדרשים "
            "לאימות נתונים בעסקאות נדל\"ן בישראל - תעודות זהות, טלפונים, תאריכים, "
            "מספרי גוש וחלקה, ועוד. אתה מייצר דוח EDA מפורט."
        ),
        tools=[validate_client_data],
        verbose=True,
    )


def create_document_processor_agent() -> Agent:
    return Agent(
        role="מעבד מסמכים",
        goal="לבצע OCR על מסמכים סרוקים, לחלץ נתונים מנסח טאבו ורשומות עירייה, ולייצר קבצי פלט נקיים",
        backstory=(
            "אתה מומחה בעיבוד מסמכים סרוקים בתחום הנדל\"ן הישראלי. "
            "אתה יודע לקרוא נסחי טאבו, תעודות רישום, ומסמכי עירייה, "
            "ולחלץ מהם מידע מובנה כגון גוש, חלקה, בעלים רשומים, שעבודים ועוד."
        ),
        tools=[process_document_ocr, clean_and_export_data],
        verbose=True,
    )
