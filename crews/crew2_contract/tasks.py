"""Crew 2 Tasks - Contract Creation and Quality Control."""

from crewai import Task, Agent


def create_contract_building_task(agent: Agent, clean_data_json: str) -> Task:
    return Task(
        description=(
            f"בנה חוזה מכר דירה מלא בעברית על סמך הנתונים הנקיים הבאים:\n"
            f"{clean_data_json}\n\n"
            "צור שני גרסאות חוזה:\n"
            "1. גרסה רגילה (standard) - תשלום ב-3 שלבים\n"
            "2. גרסה עם משכנתא (mortgage) - תשלום ב-4 שלבים כולל משכנתא\n"
            "שמור את שתי הגרסאות כקבצי DOCX בתיקיית artifacts."
        ),
        expected_output="נתיבים לקבצי החוזה שנוצרו (שתי גרסאות)",
        agent=agent,
    )


def create_compliance_check_task(agent: Agent, clean_data_json: str) -> Task:
    return Task(
        description=(
            f"בדוק את תאימות החוזה לחוקי המקרקעין הישראליים:\n"
            f"{clean_data_json}\n\n"
            "בדוק בפרט:\n"
            "- חוק מכר דירות (הבטחת השקעות של רוכשי דירות), תשל\"ג-1973\n"
            "- חוק המקרקעין\n"
            "- חוק מיסוי מקרקעין\n"
            "- חוק התכנון והבנייה\n"
            "צור דוח הערכה מפורט (evaluation_report.md)."
        ),
        expected_output="תוצאות בדיקת התאימות בפורמט JSON ונתיב לדוח ההערכה",
        agent=agent,
    )


def create_quality_scoring_task(agent: Agent, clean_data_json: str, compliance_json: str) -> Task:
    return Task(
        description=(
            f"העריך את איכות החוזה ותן ציון 0-100.\n"
            f"נתוני העסקה:\n{clean_data_json}\n\n"
            f"תוצאות בדיקת תאימות:\n{compliance_json}\n\n"
            "צור כרטיס חוזה (contract_card.md) הכולל:\n"
            "- מטרת החוזה\n"
            "- סיכום נתוני העסקה\n"
            "- ציון איכות והמלצה\n"
            "- מגבלות\n"
            "- שיקולים אתיים"
        ),
        expected_output="ציון איכות ונתיב לכרטיס החוזה",
        agent=agent,
    )
