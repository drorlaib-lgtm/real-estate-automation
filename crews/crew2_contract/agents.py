"""Crew 2 Agents - Contract Creation and Quality Control Team."""

from crewai import Agent

from crews.crew2_contract.tools.contract_builder import build_contract
from crews.crew2_contract.tools.legal_compliance import check_legal_compliance
from crews.crew2_contract.tools.quality_scorer import score_contract_quality


def create_contract_builder_agent() -> Agent:
    return Agent(
        role="בונה חוזים",
        goal="לבנות חוזה מכר דירה מלא ותקני בעברית, בפורמט DOCX",
        backstory=(
            "אתה עורך דין מומחה בנדל\"ן עם ניסיון רב בעריכת חוזי מכר דירות. "
            "אתה יודע ליצור חוזים מקצועיים הכוללים את כל הסעיפים הנדרשים "
            "על פי חוק מכר דירות ועל פי הפרקטיקה המקובלת בישראל."
        ),
        tools=[build_contract],
        verbose=True,
    )


def create_legal_compliance_agent() -> Agent:
    return Agent(
        role="בודק תאימות משפטית",
        goal="לבדוק את החוזה מול חוק מכר דירות 1973 ודרישות חוקיות נוספות",
        backstory=(
            "אתה מומחה בדיני מקרקעין ובחוק מכר דירות (הבטחת השקעות של רוכשי דירות), תשל\"ג-1973. "
            "אתה בודק חוזים בקפדנות ומוודא שכל הדרישות החוקיות מתקיימות."
        ),
        tools=[check_legal_compliance],
        verbose=True,
    )


def create_quality_assurance_agent() -> Agent:
    return Agent(
        role="בקרת איכות",
        goal="להעריך את איכות החוזה, לתת ציון 0-100, וליצור כרטיס חוזה מסכם",
        backstory=(
            "אתה מומחה בבקרת איכות של מסמכים משפטיים. "
            "אתה בודק שלמות, דיוק, תאימות חוקית, וגורמי סיכון, "
            "ומסכם את הכל בכרטיס חוזה ברור ומקיף."
        ),
        tools=[score_contract_quality],
        verbose=True,
    )
