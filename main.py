"""
Real Estate Contract Automation System - CrewAI Flow Orchestrator
=================================================================
Coordinates between Crew 1 (Data Collection) and Crew 2 (Contract Creation).
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from crewai.flow.flow import Flow, listen, start, router

from crews.crew1_data.tools.form_generator import generate_client_form
from crews.crew1_data.tools.validator import run_validation, generate_eda_report
from crews.crew1_data.tools.ocr_processor import extract_text_from_image, parse_tabu_document, parse_municipal_document
from crews.crew1_data.tools.data_cleaner import merge_and_clean, generate_dataset_contract
from crews.crew2_contract.tools.contract_builder import build_contract_document
from crews.crew2_contract.tools.legal_compliance import run_compliance_check, generate_evaluation_report
from crews.crew2_contract.tools.quality_scorer import calculate_quality_score, generate_contract_card

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("artifacts/flow.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


# Sample data for demonstration
SAMPLE_CLIENT_DATA = {
    "seller_name": "ישראל ישראלי",
    "seller_id": "123456782",
    "seller_address": "רחוב הרצל 10, תל אביב",
    "seller_phone": "0501234567",
    "seller_email": "seller@example.com",
    "seller_marital_status": "married",
    "buyer_name": "משה כהן",
    "buyer_id": "987654321",
    "buyer_address": "רחוב בן גוריון 5, חיפה",
    "buyer_phone": "0529876543",
    "buyer_email": "buyer@example.com",
    "property_address": "רחוב ויצמן 15, דירה 8, רמת גן",
    "block_number": "6123",
    "parcel_number": "456",
    "sub_parcel": "8",
    "area_sqm": "95",
    "rooms": "4",
    "floor": "3",
    "property_type": "apartment",
    "parking": "covered",
    "storage": "yes",
    "price": "2500000",
    "signing_date": "2026-03-01",
    "delivery_date": "2026-06-01",
    "notes": "הדירה כוללת מזגן בכל חדר ומטבח משופץ",
}


class RealEstateFlow(Flow):
    """CrewAI Flow that orchestrates the real estate contract automation pipeline."""

    def __init__(self, client_data: dict = None, document_paths: list = None):
        super().__init__()
        self.client_data = client_data or SAMPLE_CLIENT_DATA
        self.document_paths = document_paths or []
        self.clean_data = {}
        self.ocr_data = {}
        self.validation_result = {}
        self.dataset_contract = {}
        self.compliance_result = {}
        self.quality_result = {}
        self.artifacts = {}

    @start()
    def generate_form(self):
        """Step 1: Generate the client intake form."""
        logger.info("=== שלב 1: יצירת טופס לקוח ===")
        os.makedirs("artifacts", exist_ok=True)
        form_path = "artifacts/client_form.html"

        from crews.crew1_data.tools.form_generator import FORM_TEMPLATE
        with open(form_path, "w", encoding="utf-8") as f:
            f.write(FORM_TEMPLATE)

        self.artifacts["form"] = form_path
        logger.info(f"טופס נוצר: {form_path}")
        return {"form_path": form_path}

    @listen(generate_form)
    def validate_data(self, form_result):
        """Step 2: Validate client data."""
        logger.info("=== שלב 2: אימות נתונים ===")

        self.validation_result = run_validation(self.client_data)
        eda_path = generate_eda_report(
            self.client_data, self.validation_result, "artifacts/eda_report.html"
        )

        self.artifacts["eda_report"] = eda_path
        logger.info(
            f"ולידציה: {self.validation_result['passed']}/{self.validation_result['total_rules']} כללים עברו"
        )

        if not self.validation_result["valid"]:
            error_msgs = [e["message"] for e in self.validation_result["errors"]]
            logger.warning(f"שגיאות ולידציה: {error_msgs}")

        return self.validation_result

    @listen(validate_data)
    def process_documents(self, validation_result):
        """Step 3: Process OCR documents and clean data."""
        logger.info("=== שלב 3: עיבוד מסמכים וניקוי נתונים ===")

        # Process OCR if documents provided
        for doc_path in self.document_paths:
            if os.path.exists(doc_path):
                logger.info(f"מעבד מסמך: {doc_path}")
                text = extract_text_from_image(doc_path)
                if "tabu" in doc_path.lower() or "טאבו" in doc_path.lower():
                    parsed = parse_tabu_document(text)
                else:
                    parsed = parse_municipal_document(text)
                self.ocr_data.update(parsed)

        # Merge and clean data
        self.clean_data = merge_and_clean(self.client_data, self.ocr_data or None)

        # Save clean_data.csv
        import pandas as pd
        df = pd.DataFrame([self.clean_data])
        csv_path = "artifacts/clean_data.csv"
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        self.artifacts["clean_data"] = csv_path

        # Generate dataset contract
        self.dataset_contract = generate_dataset_contract(self.clean_data)
        contract_path = "artifacts/dataset_contract.json"
        with open(contract_path, "w", encoding="utf-8") as f:
            json.dump(self.dataset_contract, f, ensure_ascii=False, indent=2)
        self.artifacts["dataset_contract"] = contract_path

        # Generate insights
        insights_path = "artifacts/insights.md"
        with open(insights_path, "w", encoding="utf-8") as f:
            f.write("# תובנות עסקיות - סיכום נתונים\n\n")
            f.write(f"## פרטי העסקה\n")
            f.write(f"- **מוכר:** {self.clean_data['seller_name']} (ת.ז. {self.clean_data['seller_id']})\n")
            f.write(f"- **קונה:** {self.clean_data['buyer_name']} (ת.ז. {self.clean_data['buyer_id']})\n")
            f.write(f"- **נכס:** {self.clean_data['property_address']}\n")
            f.write(f"- **גוש/חלקה:** {self.clean_data['block_number']}/{self.clean_data['parcel_number']}\n")
            f.write(f"- **שטח:** {self.clean_data['area_sqm']} מ\"ר\n")
            f.write(f"- **חדרים:** {self.clean_data['rooms']}\n")
            f.write(f"- **מחיר:** {self.clean_data['price']:,.0f} ₪\n")
            f.write(f"- **מחיר למ\"ר:** {self.clean_data['price_per_sqm']:,.0f} ₪\n\n")
            f.write(f"## סטטוס משפטי\n")
            f.write(f"- משכנתא: {'כן' if self.clean_data.get('has_mortgage') else 'לא'}\n")
            f.write(f"- עיקול: {'כן' if self.clean_data.get('has_lien') else 'לא'}\n")
            f.write(f"- הערת אזהרה: {'כן' if self.clean_data.get('has_warning_note') else 'לא'}\n")
            f.write(f"- חריגות בנייה: {'כן' if self.clean_data.get('has_violations') else 'לא'}\n\n")
            f.write(f"## לוח זמנים\n")
            f.write(f"- תאריך חתימה: {self.clean_data['signing_date']}\n")
            f.write(f"- תאריך מסירה: {self.clean_data['delivery_date']}\n\n")
            f.write(f"---\n*נוצר אוטומטית: {datetime.now().isoformat()}*\n")
        self.artifacts["insights"] = insights_path

        logger.info(f"נתונים נוקו ונשמרו: {csv_path}")
        return self.clean_data

    @listen(process_documents)
    def validate_dataset_contract(self, clean_data):
        """Step 4: Validate dataset contract compliance before passing to Crew 2."""
        logger.info("=== שלב 4: בדיקת תאימות Dataset Contract ===")

        schema = self.dataset_contract.get("schema", {})
        issues = []

        for field_name, field_spec in schema.items():
            value = clean_data.get(field_name)
            if field_spec.get("required") and not value:
                issues.append(f"שדה חובה חסר: {field_name}")

        if issues:
            logger.warning(f"בעיות בתאימות Dataset Contract: {issues}")
            # Graceful - continue but log warnings
        else:
            logger.info("Dataset Contract תקין - ממשיכים ליצירת חוזה")

        return {"valid": len(issues) == 0, "issues": issues}

    @listen(validate_dataset_contract)
    def build_contracts(self, validation_gate):
        """Step 5: Build contract documents (2 variations)."""
        logger.info("=== שלב 5: בניית חוזים ===")

        # Generate features.csv
        import pandas as pd
        features = {
            "price_per_sqm": self.clean_data.get("price_per_sqm", 0),
            "has_parking": 1 if self.clean_data.get("parking", "none") != "none" else 0,
            "has_storage": 1 if self.clean_data.get("storage") == "yes" else 0,
            "floor": self.clean_data.get("floor", 0),
            "rooms": self.clean_data.get("rooms", 0),
            "area_sqm": self.clean_data.get("area_sqm", 0),
            "has_mortgage": 1 if self.clean_data.get("has_mortgage") else 0,
            "has_lien": 1 if self.clean_data.get("has_lien") else 0,
            "has_violations": 1 if self.clean_data.get("has_violations") else 0,
            "property_type": self.clean_data.get("property_type", ""),
        }
        features_df = pd.DataFrame([features])
        features_path = "artifacts/features.csv"
        features_df.to_csv(features_path, index=False)
        self.artifacts["features"] = features_path

        # Build standard contract
        doc_standard = build_contract_document(self.clean_data, "standard")
        standard_path = "artifacts/contract_standard.docx"
        doc_standard.save(standard_path)
        self.artifacts["contract_standard"] = standard_path
        logger.info(f"חוזה רגיל נוצר: {standard_path}")

        # Build mortgage variation
        doc_mortgage = build_contract_document(self.clean_data, "mortgage")
        mortgage_path = "artifacts/contract_mortgage.docx"
        doc_mortgage.save(mortgage_path)
        self.artifacts["contract_mortgage"] = mortgage_path
        logger.info(f"חוזה משכנתא נוצר: {mortgage_path}")

        # Copy standard as main contract.docx
        doc_main = build_contract_document(self.clean_data, "standard")
        main_path = "artifacts/contract.docx"
        doc_main.save(main_path)
        self.artifacts["contract"] = main_path

        return {"standard": standard_path, "mortgage": mortgage_path}

    @listen(build_contracts)
    def check_compliance(self, contracts):
        """Step 6: Check legal compliance."""
        logger.info("=== שלב 6: בדיקת תאימות משפטית ===")

        self.compliance_result = run_compliance_check(self.clean_data)
        report_path = generate_evaluation_report(
            self.compliance_result, "artifacts/evaluation_report.md"
        )

        self.artifacts["evaluation_report"] = report_path
        logger.info(
            f"תאימות: {self.compliance_result['passed']}/{self.compliance_result['total_checks']} | "
            f"תקין: {self.compliance_result['compliant']}"
        )
        return self.compliance_result

    @listen(check_compliance)
    def score_quality(self, compliance):
        """Step 7: Score quality and generate contract card."""
        logger.info("=== שלב 7: ציון איכות וכרטיס חוזה ===")

        self.quality_result = calculate_quality_score(self.clean_data, compliance)
        card_path = generate_contract_card(
            self.clean_data, self.quality_result, compliance, "artifacts/contract_card.md"
        )

        self.artifacts["contract_card"] = card_path
        logger.info(f"ציון איכות: {self.quality_result['score']}/100 - {self.quality_result['grade']}")
        return self.quality_result

    @listen(score_quality)
    def finalize(self, quality):
        """Step 8: Final summary."""
        logger.info("=== שלב 8: סיכום סופי ===")

        summary = {
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "quality_score": quality["score"],
            "quality_grade": quality["grade"],
            "recommendation": quality["recommendation"],
            "compliant": self.compliance_result.get("compliant", False),
            "validation_passed": self.validation_result.get("valid", False),
            "artifacts": self.artifacts,
        }

        summary_path = "artifacts/flow_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        logger.info("=" * 50)
        logger.info("🏠 תהליך אוטומציית חוזי נדל\"ן הושלם!")
        logger.info(f"   ציון: {quality['score']}/100 ({quality['grade']})")
        logger.info(f"   המלצה: {quality['recommendation']}")
        logger.info(f"   קבצים שנוצרו: {len(self.artifacts)}")
        logger.info("=" * 50)

        return summary


def run_flow(client_data: dict = None, document_paths: list = None):
    """Run the complete real estate automation flow."""
    flow = RealEstateFlow(client_data=client_data, document_paths=document_paths)
    result = flow.kickoff()
    return result


if __name__ == "__main__":
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    print("מפעיל מערכת אוטומציית חוזי נדל\"ן...")
    print("=" * 50)
    result = run_flow()
    print("\nהתהליך הושלם!")
    print(f"ציון איכות: {result.get('quality_score', 'N/A')}/100")
    print(f"קבצים נוצרו בתיקיית artifacts/")
