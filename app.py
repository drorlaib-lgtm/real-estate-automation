"""
Real Estate Contract Automation - Streamlit UI (Hebrew RTL)
===========================================================
"""

import os
import sys
import json
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from crews.crew1_data.tools.validator import run_validation, generate_eda_report
from crews.crew1_data.tools.ocr_processor import extract_text_from_image, parse_tabu_document, parse_municipal_document
from crews.crew1_data.tools.data_cleaner import merge_and_clean, generate_dataset_contract
from crews.crew2_contract.tools.contract_builder import build_contract_document
from crews.crew2_contract.tools.legal_compliance import run_compliance_check, generate_evaluation_report
from crews.crew2_contract.tools.quality_scorer import calculate_quality_score, generate_contract_card

# Page config
st.set_page_config(
    page_title="מערכת אוטומציית חוזי נדל\"ן",
    page_icon="🏠",
    layout="wide",
)

# RTL CSS
st.markdown("""
<style>
    .stApp { direction: rtl; }
    .stMarkdown, .stText, label, .stSelectbox, .stTextInput, .stNumberInput { direction: rtl; text-align: right; }
    h1, h2, h3 { text-align: center; }
    .stProgress > div > div { direction: ltr; }
</style>
""", unsafe_allow_html=True)

st.title("🏠 מערכת אוטומציית חוזי נדל\"ן")
st.markdown("---")

# Sidebar
st.sidebar.header("ניווט")
page = st.sidebar.radio("בחר שלב:", [
    "📝 הזנת נתונים",
    "📄 העלאת מסמכים",
    "✅ אימות נתונים",
    "📋 יצירת חוזה",
    "📊 דוחות ותוצאות",
])

# Initialize session state
if "client_data" not in st.session_state:
    st.session_state.client_data = {}
if "ocr_data" not in st.session_state:
    st.session_state.ocr_data = {}
if "clean_data" not in st.session_state:
    st.session_state.clean_data = {}
if "validation_result" not in st.session_state:
    st.session_state.validation_result = {}
if "compliance_result" not in st.session_state:
    st.session_state.compliance_result = {}
if "quality_result" not in st.session_state:
    st.session_state.quality_result = {}
if "flow_completed" not in st.session_state:
    st.session_state.flow_completed = False


if page == "📝 הזנת נתונים":
    st.header("📝 הזנת פרטי העסקה")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("פרטי המוכר")
        seller_name = st.text_input("שם מלא *", key="seller_name")
        seller_id = st.text_input("תעודת זהות *", key="seller_id")
        seller_address = st.text_input("כתובת *", key="seller_address")
        seller_phone = st.text_input("טלפון *", placeholder="05XXXXXXXX", key="seller_phone")
        seller_email = st.text_input("דוא\"ל *", key="seller_email")
        seller_marital = st.selectbox("מצב משפחתי", ["", "רווק/ה", "נשוי/אה", "גרוש/ה", "אלמן/ה"], key="seller_marital")
        marital_map = {"": "", "רווק/ה": "single", "נשוי/אה": "married", "גרוש/ה": "divorced", "אלמן/ה": "widowed"}

    with col2:
        st.subheader("פרטי הקונה")
        buyer_name = st.text_input("שם מלא *", key="buyer_name")
        buyer_id = st.text_input("תעודת זהות *", key="buyer_id")
        buyer_address = st.text_input("כתובת *", key="buyer_address")
        buyer_phone = st.text_input("טלפון *", placeholder="05XXXXXXXX", key="buyer_phone")
        buyer_email = st.text_input("דוא\"ל *", key="buyer_email")

    st.subheader("פרטי הנכס")
    col3, col4 = st.columns(2)
    with col3:
        property_address = st.text_input("כתובת הנכס *", key="prop_addr")
        block_number = st.text_input("גוש *", key="block")
        parcel_number = st.text_input("חלקה *", key="parcel")
        sub_parcel = st.text_input("תת-חלקה", key="sub_parcel")
    with col4:
        area_sqm = st.number_input("שטח (מ\"ר) *", min_value=10, max_value=5000, value=80, key="area")
        rooms = st.number_input("חדרים *", min_value=1.0, max_value=20.0, value=3.0, step=0.5, key="rooms_input")
        floor = st.number_input("קומה", min_value=-2, max_value=100, value=0, key="floor_input")
        prop_type = st.selectbox("סוג נכס *", ["דירה", "פנטהאוז", "דירת גן", "דופלקס", "בית פרטי", "מגרש"], key="prop_type")
        type_map = {"דירה": "apartment", "פנטהאוז": "penthouse", "דירת גן": "garden", "דופלקס": "duplex", "בית פרטי": "house", "מגרש": "land"}

    col5, col6 = st.columns(2)
    with col5:
        parking = st.selectbox("חניה", ["ללא", "מקורה", "לא מקורה", "תת-קרקעית"], key="parking_input")
        parking_map = {"ללא": "none", "מקורה": "covered", "לא מקורה": "uncovered", "תת-קרקעית": "underground"}
    with col6:
        storage = st.selectbox("מחסן", ["לא", "כן"], key="storage_input")

    st.subheader("פרטי העסקה")
    col7, col8 = st.columns(2)
    with col7:
        price = st.number_input("מחיר (₪) *", min_value=50000, max_value=100000000, value=1500000, step=50000, key="price_input")
        signing_date = st.date_input("תאריך חתימה *", value=date.today() + timedelta(days=7), key="sign_date")
    with col8:
        delivery_date = st.date_input("תאריך מסירה *", value=date.today() + timedelta(days=90), key="del_date")
    notes = st.text_area("הערות נוספות", key="notes_input")

    if st.button("💾 שמור נתונים", type="primary"):
        st.session_state.client_data = {
            "seller_name": seller_name, "seller_id": seller_id,
            "seller_address": seller_address, "seller_phone": seller_phone,
            "seller_email": seller_email, "seller_marital_status": marital_map.get(seller_marital, ""),
            "buyer_name": buyer_name, "buyer_id": buyer_id,
            "buyer_address": buyer_address, "buyer_phone": buyer_phone,
            "buyer_email": buyer_email,
            "property_address": property_address, "block_number": block_number,
            "parcel_number": parcel_number, "sub_parcel": sub_parcel,
            "area_sqm": str(area_sqm), "rooms": str(rooms), "floor": str(floor),
            "property_type": type_map.get(prop_type, "apartment"),
            "parking": parking_map.get(parking, "none"),
            "storage": "yes" if storage == "כן" else "no",
            "price": str(price),
            "signing_date": signing_date.strftime("%Y-%m-%d"),
            "delivery_date": delivery_date.strftime("%Y-%m-%d"),
            "notes": notes,
        }
        st.success("הנתונים נשמרו בהצלחה!")


elif page == "📄 העלאת מסמכים":
    st.header("📄 העלאת מסמכים סרוקים")

    uploaded_tabu = st.file_uploader("נסח טאבו (תמונה סרוקה)", type=["png", "jpg", "jpeg", "tiff", "bmp"], key="tabu")
    uploaded_municipal = st.file_uploader("מסמך עירייה (תמונה סרוקה)", type=["png", "jpg", "jpeg", "tiff", "bmp"], key="municipal")

    if st.button("🔍 עבד מסמכים (OCR)", type="primary"):
        os.makedirs("artifacts", exist_ok=True)
        ocr_results = {}

        if uploaded_tabu:
            tabu_path = f"artifacts/uploaded_tabu.{uploaded_tabu.name.split('.')[-1]}"
            with open(tabu_path, "wb") as f:
                f.write(uploaded_tabu.read())
            st.info("מעבד נסח טאבו...")
            text = extract_text_from_image(tabu_path)
            parsed = parse_tabu_document(text)
            ocr_results.update(parsed)
            st.json(parsed)

        if uploaded_municipal:
            muni_path = f"artifacts/uploaded_municipal.{uploaded_municipal.name.split('.')[-1]}"
            with open(muni_path, "wb") as f:
                f.write(uploaded_municipal.read())
            st.info("מעבד מסמך עירייה...")
            text = extract_text_from_image(muni_path)
            parsed = parse_municipal_document(text)
            ocr_results.update(parsed)
            st.json(parsed)

        if ocr_results:
            st.session_state.ocr_data = ocr_results
            st.success(f"עובדו {len(ocr_results)} שדות מהמסמכים")
        else:
            st.warning("לא הועלו מסמכים")


elif page == "✅ אימות נתונים":
    st.header("✅ אימות נתונים")

    if not st.session_state.client_data:
        st.warning("יש להזין נתונים תחילה בשלב 'הזנת נתונים'")
    else:
        if st.button("🔍 בצע אימות", type="primary"):
            result = run_validation(st.session_state.client_data)
            st.session_state.validation_result = result

            score = round(result["passed"] / max(result["total_rules"], 1) * 100, 1)
            st.metric("ציון איכות נתונים", f"{score}%")
            st.progress(score / 100)

            if result["valid"]:
                st.success(f"כל {result['total_rules']} הכללים עברו בהצלחה!")
            else:
                st.error(f"נמצאו {len(result['errors'])} שגיאות:")
                for err in result["errors"]:
                    st.markdown(f"- ❌ **{err['field']}**: {err['message']}")

            if result["warnings"]:
                st.warning(f"נמצאו {len(result['warnings'])} אזהרות:")
                for warn in result["warnings"]:
                    st.markdown(f"- ⚠️ **{warn['field']}**: {warn['message']}")

            # Generate EDA report
            os.makedirs("artifacts", exist_ok=True)
            generate_eda_report(st.session_state.client_data, result, "artifacts/eda_report.html")
            st.info("דוח EDA נשמר: artifacts/eda_report.html")


elif page == "📋 יצירת חוזה":
    st.header("📋 יצירת חוזה")

    if not st.session_state.client_data:
        st.warning("יש להזין נתונים תחילה")
    else:
        if st.button("🚀 הפעל תהליך מלא", type="primary"):
            progress = st.progress(0)
            status = st.empty()

            # Step 1: Clean data
            status.text("שלב 1/5: ניקוי ומיזוג נתונים...")
            progress.progress(20)
            clean_data = merge_and_clean(
                st.session_state.client_data,
                st.session_state.ocr_data or None,
            )
            st.session_state.clean_data = clean_data
            os.makedirs("artifacts", exist_ok=True)

            # Save clean_data.csv
            pd.DataFrame([clean_data]).to_csv("artifacts/clean_data.csv", index=False, encoding="utf-8-sig")

            # Save dataset_contract.json
            ds_contract = generate_dataset_contract(clean_data)
            with open("artifacts/dataset_contract.json", "w", encoding="utf-8") as f:
                json.dump(ds_contract, f, ensure_ascii=False, indent=2)

            # Step 2: Build contracts
            status.text("שלב 2/5: בניית חוזים...")
            progress.progress(40)

            # Features
            features = {
                "price_per_sqm": clean_data.get("price_per_sqm", 0),
                "has_parking": 1 if clean_data.get("parking", "none") != "none" else 0,
                "has_storage": 1 if clean_data.get("storage") == "yes" else 0,
                "floor": clean_data.get("floor", 0),
                "rooms": clean_data.get("rooms", 0),
                "area_sqm": clean_data.get("area_sqm", 0),
            }
            pd.DataFrame([features]).to_csv("artifacts/features.csv", index=False)

            doc_std = build_contract_document(clean_data, "standard")
            doc_std.save("artifacts/contract.docx")
            doc_std.save("artifacts/contract_standard.docx")
            doc_mtg = build_contract_document(clean_data, "mortgage")
            doc_mtg.save("artifacts/contract_mortgage.docx")

            # Step 3: Legal compliance
            status.text("שלב 3/5: בדיקת תאימות משפטית...")
            progress.progress(60)
            compliance = run_compliance_check(clean_data)
            st.session_state.compliance_result = compliance
            generate_evaluation_report(compliance, "artifacts/evaluation_report.md")

            # Step 4: Quality score
            status.text("שלב 4/5: הערכת איכות...")
            progress.progress(80)
            quality = calculate_quality_score(clean_data, compliance)
            st.session_state.quality_result = quality
            generate_contract_card(clean_data, quality, compliance, "artifacts/contract_card.md")

            # Step 5: Done
            status.text("שלב 5/5: סיכום...")
            progress.progress(100)
            st.session_state.flow_completed = True

            st.success("התהליך הושלם בהצלחה!")
            st.metric("ציון איכות חוזה", f"{quality['score']}/100")
            st.info(f"דרגה: {quality['grade']} | המלצה: {quality['recommendation']}")


elif page == "📊 דוחות ותוצאות":
    st.header("📊 דוחות ותוצאות")

    if not st.session_state.flow_completed:
        st.warning("יש להפעיל תחילה את תהליך יצירת החוזה")
    else:
        st.subheader("קבצים שנוצרו")

        artifacts_dir = Path("artifacts")
        artifact_files = {
            "contract.docx": "חוזה מכר (רגיל)",
            "contract_standard.docx": "חוזה - גרסה רגילה",
            "contract_mortgage.docx": "חוזה - גרסה עם משכנתא",
            "clean_data.csv": "נתונים נקיים",
            "features.csv": "פיצ'רים",
            "dataset_contract.json": "חוזה מערכת נתונים",
            "eda_report.html": "דוח EDA",
            "evaluation_report.md": "דוח הערכה משפטית",
            "contract_card.md": "כרטיס חוזה",
            "insights.md": "תובנות עסקיות",
        }

        for filename, label in artifact_files.items():
            filepath = artifacts_dir / filename
            if filepath.exists():
                with open(filepath, "rb") as f:
                    st.download_button(
                        label=f"📥 הורד: {label}",
                        data=f.read(),
                        file_name=filename,
                        key=f"dl_{filename}",
                    )

        # Show quality summary
        if st.session_state.quality_result:
            st.subheader("סיכום איכות")
            q = st.session_state.quality_result
            col1, col2, col3 = st.columns(3)
            col1.metric("ציון", f"{q['score']}/100")
            col2.metric("דרגה", q["grade"])
            col3.metric("המלצה", q["recommendation"])

        # Show contract card
        card_path = artifacts_dir / "contract_card.md"
        if card_path.exists():
            st.subheader("כרטיס חוזה")
            st.markdown(card_path.read_text(encoding="utf-8"))

        # Show evaluation report
        eval_path = artifacts_dir / "evaluation_report.md"
        if eval_path.exists():
            st.subheader("דוח הערכה משפטית")
            st.markdown(eval_path.read_text(encoding="utf-8"))
