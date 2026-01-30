# מערכת אוטומציית חוזי נדל"ן
## Real Estate Contract Automation System

פרויקט גמר - קורס פיתוח AI ושיתוף פעולה

**מפתחים:** מאיר (סוכן נדל"ן) + דרור (עורך דין נדל"ן)

---

## תיאור הפרויקט

מערכת המבוססת על CrewAI Flow המתאמת בין שני צוותי סוכנים:

### Crew 1 — צוות איסוף ואימות נתונים (מאיר)
| סוכן | תפקיד |
|-------|--------|
| Form Generator | יצירת טפסי HTML בעברית RTL |
| Data Validator | אימות 50+ כללים, כולל ת.ז. ישראלית |
| Document Processor | OCR על נסח טאבו ומסמכי עירייה |

### Crew 2 — צוות יצירת חוזים ובקרת איכות (דרור)
| סוכן | תפקיד |
|-------|--------|
| Contract Builder | בניית חוזה מכר בעברית (DOCX) |
| Legal Compliance | בדיקת חוק מכר דירות 1973 |
| Quality Assurance | ציון איכות 0-100, כרטיס חוזה |

## התקנה

```bash
cd real-estate-automation
pip install -r requirements.txt
```

להגדרת Tesseract OCR (לעיבוד מסמכים סרוקים):
- Windows: https://github.com/UB-Mannheim/tesseract/wiki
- יש להוסיף את הנתיב ל-PATH

## הפעלה

### Flow מלא (CLI)
```bash
# הגדר מפתח API
set ANTHROPIC_API_KEY=your_key_here

# הפעל
python main.py
```

### ממשק Streamlit
```bash
streamlit run app.py
```

### טסטים
```bash
pytest tests/ -v
```

## קבצי פלט (artifacts/)

| קובץ | תיאור |
|-------|--------|
| `client_form.html` | טופס איסוף נתונים |
| `clean_data.csv` | נתונים נקיים |
| `eda_report.html` | דוח ניתוח נתונים |
| `insights.md` | תובנות עסקיות |
| `dataset_contract.json` | חוזה מערכת נתונים |
| `features.csv` | פיצ'רים |
| `contract.docx` | חוזה מכר |
| `contract_standard.docx` | גרסה רגילה |
| `contract_mortgage.docx` | גרסה עם משכנתא |
| `evaluation_report.md` | דוח תאימות משפטית |
| `contract_card.md` | כרטיס חוזה |

## טכנולוגיות

CrewAI, Python, Streamlit, Pandas, python-docx, pytesseract, Matplotlib, Scikit-learn

## מבנה הפרויקט

```
real-estate-automation/
├── main.py              # Flow orchestrator
├── app.py               # Streamlit UI
├── config/              # YAML configs
├── crews/
│   ├── crew1_data/      # Crew 1 - Data
│   │   ├── agents.py
│   │   ├── tasks.py
│   │   ├── crew.py
│   │   └── tools/       # 4 tools
│   └── crew2_contract/  # Crew 2 - Contract
│       ├── agents.py
│       ├── tasks.py
│       ├── crew.py
│       └── tools/       # 3 tools
├── templates/
├── data/
├── artifacts/           # Output
└── tests/
```
