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

# RTL CSS + Drag & Drop styling
st.markdown("""
<style>
    .stApp { direction: rtl; }
    .stMarkdown, .stText, label, .stSelectbox, .stTextInput, .stNumberInput { direction: rtl; text-align: right; }
    h1, h2, h3 { text-align: center; }
    .stProgress > div > div { direction: ltr; }
    /* Drag and drop styling */
    .uploadedFile { direction: ltr; }
    [data-testid="stFileUploader"] {
        border: 2px dashed #ccc;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #1f77b4;
        background-color: #f0f8ff;
    }
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

# Initialize session state - PERSISTENT across pages
if "sellers" not in st.session_state:
    st.session_state.sellers = [{"name": "", "id": "", "address": "", "phone": "", "email": "", "marital_status": ""}]
if "buyers" not in st.session_state:
    st.session_state.buyers = [{"name": "", "id": "", "address": "", "phone": "", "email": "", "marital_status": ""}]
if "property_data" not in st.session_state:
    st.session_state.property_data = {}
if "transaction_data" not in st.session_state:
    st.session_state.transaction_data = {}
if "seller_notes" not in st.session_state:
    st.session_state.seller_notes = ""
if "uploaded_docs" not in st.session_state:
    st.session_state.uploaded_docs = {
        "seller_ids": [],
        "buyer_ids": [],
        "tabu": None,
        "municipal": None,
        "arnona": None,
        "purchase_agreement": None,
        "other": []
    }
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

# Marital status mapping
MARITAL_OPTIONS = ["", "רווק/ה", "נשוי/אה", "גרוש/ה", "אלמן/ה"]
MARITAL_MAP = {"": "", "רווק/ה": "single", "נשוי/אה": "married", "גרוש/ה": "divorced", "אלמן/ה": "widowed"}
MARITAL_MAP_REVERSE = {v: k for k, v in MARITAL_MAP.items()}

# Supported file types for uploads
SUPPORTED_FILE_TYPES = ["png", "jpg", "jpeg", "tiff", "bmp", "pdf", "doc", "docx"]


def render_person_form(person_type: str, index: int, data: dict) -> dict:
    """Render form fields for a person (seller/buyer) and return updated data."""
    prefix = f"{person_type}_{index}"

    col1, col2 = st.columns(2)
    with col1:
        data["name"] = st.text_input("שם מלא *", value=data.get("name", ""), key=f"{prefix}_name")
        data["id"] = st.text_input("תעודת זהות *", value=data.get("id", ""), key=f"{prefix}_id")
        data["address"] = st.text_input("כתובת *", value=data.get("address", ""), key=f"{prefix}_address")
    with col2:
        data["phone"] = st.text_input("טלפון *", value=data.get("phone", ""), placeholder="05XXXXXXXX", key=f"{prefix}_phone")
        data["email"] = st.text_input("דוא\"ל *", value=data.get("email", ""), key=f"{prefix}_email")
        current_marital = MARITAL_MAP_REVERSE.get(data.get("marital_status", ""), "")
        marital_index = MARITAL_OPTIONS.index(current_marital) if current_marital in MARITAL_OPTIONS else 0
        marital = st.selectbox("מצב משפחתי *", MARITAL_OPTIONS, index=marital_index, key=f"{prefix}_marital")
        data["marital_status"] = MARITAL_MAP.get(marital, "")

    return data


if page == "📝 הזנת נתונים":
    st.header("📝 הזנת פרטי העסקה")

    # === SELLERS SECTION ===
    st.subheader("פרטי המוכרים")

    num_sellers = len(st.session_state.sellers)

    for i in range(num_sellers):
        with st.expander(f"מוכר {i + 1}" + (f" - {st.session_state.sellers[i].get('name', '')}" if st.session_state.sellers[i].get('name') else ""), expanded=(i == 0)):
            st.session_state.sellers[i] = render_person_form("seller", i, st.session_state.sellers[i])

            if num_sellers > 1:
                if st.button(f"🗑️ הסר מוכר {i + 1}", key=f"remove_seller_{i}"):
                    st.session_state.sellers.pop(i)
                    st.rerun()

    if st.button("➕ הוסף מוכר נוסף", key="add_seller"):
        st.session_state.sellers.append({"name": "", "id": "", "address": "", "phone": "", "email": "", "marital_status": ""})
        st.rerun()

    st.markdown("---")

    # === BUYERS SECTION ===
    st.subheader("פרטי הקונים")

    num_buyers = len(st.session_state.buyers)

    for i in range(num_buyers):
        with st.expander(f"קונה {i + 1}" + (f" - {st.session_state.buyers[i].get('name', '')}" if st.session_state.buyers[i].get('name') else ""), expanded=(i == 0)):
            st.session_state.buyers[i] = render_person_form("buyer", i, st.session_state.buyers[i])

            if num_buyers > 1:
                if st.button(f"🗑️ הסר קונה {i + 1}", key=f"remove_buyer_{i}"):
                    st.session_state.buyers.pop(i)
                    st.rerun()

    if st.button("➕ הוסף קונה נוסף", key="add_buyer"):
        st.session_state.buyers.append({"name": "", "id": "", "address": "", "phone": "", "email": "", "marital_status": ""})
        st.rerun()

    st.markdown("---")

    # === PROPERTY SECTION ===
    st.subheader("פרטי הנכס")
    prop = st.session_state.property_data

    col3, col4 = st.columns(2)
    with col3:
        prop["address"] = st.text_input("כתובת הנכס *", value=prop.get("address", ""), key="prop_addr")
        prop["block_number"] = st.text_input("גוש *", value=prop.get("block_number", ""), key="block")
        prop["parcel_number"] = st.text_input("חלקה *", value=prop.get("parcel_number", ""), key="parcel")
        prop["sub_parcel"] = st.text_input("תת-חלקה", value=prop.get("sub_parcel", ""), key="sub_parcel")
    with col4:
        prop["area_sqm"] = st.number_input("שטח (מ\"ר) *", min_value=10, max_value=5000, value=int(prop.get("area_sqm", 80)), key="area")
        prop["rooms"] = st.number_input("חדרים *", min_value=1.0, max_value=20.0, value=float(prop.get("rooms", 3.0)), step=0.5, key="rooms_input")
        prop["floor"] = st.number_input("קומה", min_value=-2, max_value=100, value=int(prop.get("floor", 0)), key="floor_input")

        prop_types = ["דירה", "פנטהאוז", "דירת גן", "דופלקס", "בית פרטי", "מגרש"]
        type_map = {"דירה": "apartment", "פנטהאוז": "penthouse", "דירת גן": "garden", "דופלקס": "duplex", "בית פרטי": "house", "מגרש": "land"}
        type_map_reverse = {v: k for k, v in type_map.items()}
        current_type = type_map_reverse.get(prop.get("property_type", "apartment"), "דירה")
        prop_type = st.selectbox("סוג נכס *", prop_types, index=prop_types.index(current_type), key="prop_type")
        prop["property_type"] = type_map.get(prop_type, "apartment")

    col5, col6 = st.columns(2)
    with col5:
        parking_options = ["ללא", "מקורה", "לא מקורה", "תת-קרקעית"]
        parking_map = {"ללא": "none", "מקורה": "covered", "לא מקורה": "uncovered", "תת-קרקעית": "underground"}
        parking_map_reverse = {v: k for k, v in parking_map.items()}
        current_parking = parking_map_reverse.get(prop.get("parking", "none"), "ללא")
        parking = st.selectbox("חניה", parking_options, index=parking_options.index(current_parking), key="parking_input")
        prop["parking"] = parking_map.get(parking, "none")
    with col6:
        storage_options = ["לא", "כן"]
        current_storage = "כן" if prop.get("storage") == "yes" else "לא"
        storage = st.selectbox("מחסן", storage_options, index=storage_options.index(current_storage), key="storage_input")
        prop["storage"] = "yes" if storage == "כן" else "no"

    st.session_state.property_data = prop

    st.markdown("---")

    # === TRANSACTION SECTION ===
    st.subheader("פרטי העסקה")
    trans = st.session_state.transaction_data

    col7, col8 = st.columns(2)
    with col7:
        trans["price"] = st.number_input("מחיר (₪) *", min_value=50000, max_value=100000000, value=int(trans.get("price", 1500000)), step=50000, key="price_input")
        default_sign_date = date.today() + timedelta(days=7)
        if trans.get("signing_date"):
            try:
                default_sign_date = date.fromisoformat(trans["signing_date"])
            except:
                pass
        trans["signing_date"] = st.date_input("תאריך חתימה *", value=default_sign_date, key="sign_date").strftime("%Y-%m-%d")
    with col8:
        default_del_date = date.today() + timedelta(days=90)
        if trans.get("delivery_date"):
            try:
                default_del_date = date.fromisoformat(trans["delivery_date"])
            except:
                pass
        trans["delivery_date"] = st.date_input("תאריך מסירה *", value=default_del_date, key="del_date").strftime("%Y-%m-%d")

    st.session_state.transaction_data = trans

    st.markdown("---")

    # === SELLER NOTES (for declaration) ===
    st.subheader("הערות המוכר (יופיעו בהצהרת המוכר בחוזה)")
    st.session_state.seller_notes = st.text_area(
        "הערות נוספות של המוכר לגבי הנכס",
        value=st.session_state.seller_notes,
        key="seller_notes_input",
        height=150,
        help="הערות אלו יוכנסו לסעיף הצהרת המוכר בהסכם הסופי"
    )

    st.markdown("---")

    # === SAVE BUTTON ===
    if st.button("💾 שמור נתונים", type="primary"):
        # Build client_data from all parts (for backward compatibility)
        # Use first seller/buyer as primary, store all in lists
        primary_seller = st.session_state.sellers[0] if st.session_state.sellers else {}
        primary_buyer = st.session_state.buyers[0] if st.session_state.buyers else {}

        st.session_state.client_data = {
            # Primary seller (backward compatible)
            "seller_name": primary_seller.get("name", ""),
            "seller_id": primary_seller.get("id", ""),
            "seller_address": primary_seller.get("address", ""),
            "seller_phone": primary_seller.get("phone", ""),
            "seller_email": primary_seller.get("email", ""),
            "seller_marital_status": primary_seller.get("marital_status", ""),
            # Primary buyer (backward compatible)
            "buyer_name": primary_buyer.get("name", ""),
            "buyer_id": primary_buyer.get("id", ""),
            "buyer_address": primary_buyer.get("address", ""),
            "buyer_phone": primary_buyer.get("phone", ""),
            "buyer_email": primary_buyer.get("email", ""),
            "buyer_marital_status": primary_buyer.get("marital_status", ""),
            # Property
            "property_address": st.session_state.property_data.get("address", ""),
            "block_number": st.session_state.property_data.get("block_number", ""),
            "parcel_number": st.session_state.property_data.get("parcel_number", ""),
            "sub_parcel": st.session_state.property_data.get("sub_parcel", ""),
            "area_sqm": str(st.session_state.property_data.get("area_sqm", "")),
            "rooms": str(st.session_state.property_data.get("rooms", "")),
            "floor": str(st.session_state.property_data.get("floor", "")),
            "property_type": st.session_state.property_data.get("property_type", "apartment"),
            "parking": st.session_state.property_data.get("parking", "none"),
            "storage": st.session_state.property_data.get("storage", "no"),
            # Transaction
            "price": str(st.session_state.transaction_data.get("price", "")),
            "signing_date": st.session_state.transaction_data.get("signing_date", ""),
            "delivery_date": st.session_state.transaction_data.get("delivery_date", ""),
            # Notes
            "notes": st.session_state.seller_notes,
            "seller_declaration_notes": st.session_state.seller_notes,
            # All parties (new format)
            "all_sellers": st.session_state.sellers,
            "all_buyers": st.session_state.buyers,
        }
        st.success("הנתונים נשמרו בהצלחה!")
        st.info(f"נשמרו: {len(st.session_state.sellers)} מוכרים, {len(st.session_state.buyers)} קונים")


elif page == "📄 העלאת מסמכים":
    st.header("📄 העלאת מסמכים")
    st.markdown("ניתן לגרור קבצים לאזור ההעלאה או ללחוץ לבחירה")
    st.markdown(f"**סוגי קבצים נתמכים:** {', '.join(SUPPORTED_FILE_TYPES).upper()}")

    st.markdown("---")

    # === REQUIRED DOCUMENTS ===
    st.subheader("📋 מסמכים נדרשים")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**תעודות זהות מוכרים**")
        seller_id_files = st.file_uploader(
            "העלה תעודות זהות של כל המוכרים",
            type=SUPPORTED_FILE_TYPES,
            accept_multiple_files=True,
            key="seller_ids_upload",
            help="גרור קבצים לכאן או לחץ לבחירה"
        )
        if seller_id_files:
            st.session_state.uploaded_docs["seller_ids"] = seller_id_files
            st.success(f"הועלו {len(seller_id_files)} קבצים")

    with col2:
        st.markdown("**תעודות זהות קונים**")
        buyer_id_files = st.file_uploader(
            "העלה תעודות זהות של כל הקונים",
            type=SUPPORTED_FILE_TYPES,
            accept_multiple_files=True,
            key="buyer_ids_upload",
            help="גרור קבצים לכאן או לחץ לבחירה"
        )
        if buyer_id_files:
            st.session_state.uploaded_docs["buyer_ids"] = buyer_id_files
            st.success(f"הועלו {len(buyer_id_files)} קבצים")

    st.markdown("---")

    # === PROPERTY DOCUMENTS ===
    st.subheader("🏠 מסמכי נכס")

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("**נסח טאבו**")
        uploaded_tabu = st.file_uploader(
            "נסח רישום מקרקעין",
            type=SUPPORTED_FILE_TYPES,
            key="tabu_upload"
        )
        if uploaded_tabu:
            st.session_state.uploaded_docs["tabu"] = uploaded_tabu

    with col4:
        st.markdown("**אישור עירייה / ועד בית**")
        uploaded_municipal = st.file_uploader(
            "מסמך עירייה או ועד בית",
            type=SUPPORTED_FILE_TYPES,
            key="municipal_upload"
        )
        if uploaded_municipal:
            st.session_state.uploaded_docs["municipal"] = uploaded_municipal

    col5, col6 = st.columns(2)

    with col5:
        st.markdown("**אישור ארנונה**")
        uploaded_arnona = st.file_uploader(
            "אישור תשלום ארנונה",
            type=SUPPORTED_FILE_TYPES,
            key="arnona_upload"
        )
        if uploaded_arnona:
            st.session_state.uploaded_docs["arnona"] = uploaded_arnona

    with col6:
        st.markdown("**חוזה רכישה קודם (אופציונלי)**")
        uploaded_purchase = st.file_uploader(
            "חוזה רכישה מקורי של המוכר",
            type=SUPPORTED_FILE_TYPES,
            key="purchase_upload"
        )
        if uploaded_purchase:
            st.session_state.uploaded_docs["purchase_agreement"] = uploaded_purchase

    st.markdown("---")

    # === OTHER DOCUMENTS ===
    st.subheader("📎 מסמכים נוספים")
    other_files = st.file_uploader(
        "העלה מסמכים נוספים רלוונטיים",
        type=SUPPORTED_FILE_TYPES,
        accept_multiple_files=True,
        key="other_upload",
        help="ניתן להעלות כל מסמך נוסף שרלוונטי לעסקה"
    )
    if other_files:
        st.session_state.uploaded_docs["other"] = other_files
        st.success(f"הועלו {len(other_files)} מסמכים נוספים")

    st.markdown("---")

    # === PROCESS OCR ===
    if st.button("🔍 עבד מסמכים (OCR)", type="primary"):
        os.makedirs("artifacts", exist_ok=True)
        ocr_results = {}

        # Process Tabu
        if st.session_state.uploaded_docs.get("tabu"):
            uploaded_tabu = st.session_state.uploaded_docs["tabu"]
            ext = uploaded_tabu.name.split('.')[-1].lower()
            tabu_path = f"artifacts/uploaded_tabu.{ext}"
            with open(tabu_path, "wb") as f:
                f.write(uploaded_tabu.read())

            if ext in ["png", "jpg", "jpeg", "tiff", "bmp"]:
                st.info("מעבד נסח טאבו...")
                text = extract_text_from_image(tabu_path)
                parsed = parse_tabu_document(text)
                ocr_results.update(parsed)
                st.json(parsed)
            else:
                st.info(f"קובץ {ext.upper()} נשמר (לא בוצע OCR)")

        # Process Municipal
        if st.session_state.uploaded_docs.get("municipal"):
            uploaded_municipal = st.session_state.uploaded_docs["municipal"]
            ext = uploaded_municipal.name.split('.')[-1].lower()
            muni_path = f"artifacts/uploaded_municipal.{ext}"
            with open(muni_path, "wb") as f:
                f.write(uploaded_municipal.read())

            if ext in ["png", "jpg", "jpeg", "tiff", "bmp"]:
                st.info("מעבד מסמך עירייה...")
                text = extract_text_from_image(muni_path)
                parsed = parse_municipal_document(text)
                ocr_results.update(parsed)
                st.json(parsed)
            else:
                st.info(f"קובץ {ext.upper()} נשמר (לא בוצע OCR)")

        # Save other documents
        for doc_type in ["arnona", "purchase_agreement"]:
            if st.session_state.uploaded_docs.get(doc_type):
                doc = st.session_state.uploaded_docs[doc_type]
                ext = doc.name.split('.')[-1].lower()
                doc_path = f"artifacts/uploaded_{doc_type}.{ext}"
                with open(doc_path, "wb") as f:
                    f.write(doc.read())
                st.info(f"נשמר: {doc_type}")

        if ocr_results:
            st.session_state.ocr_data = ocr_results
            st.success(f"עובדו {len(ocr_results)} שדות מהמסמכים")
        else:
            st.info("המסמכים נשמרו בהצלחה")

    # Show summary of uploaded documents
    st.markdown("---")
    st.subheader("סיכום מסמכים שהועלו")
    docs = st.session_state.uploaded_docs
    summary = []
    if docs.get("seller_ids"):
        summary.append(f"✅ תעודות זהות מוכרים: {len(docs['seller_ids'])}")
    if docs.get("buyer_ids"):
        summary.append(f"✅ תעודות זהות קונים: {len(docs['buyer_ids'])}")
    if docs.get("tabu"):
        summary.append("✅ נסח טאבו")
    if docs.get("municipal"):
        summary.append("✅ מסמך עירייה")
    if docs.get("arnona"):
        summary.append("✅ אישור ארנונה")
    if docs.get("purchase_agreement"):
        summary.append("✅ חוזה רכישה קודם")
    if docs.get("other"):
        summary.append(f"✅ מסמכים נוספים: {len(docs['other'])}")

    if summary:
        for item in summary:
            st.markdown(item)
    else:
        st.info("טרם הועלו מסמכים")


elif page == "✅ אימות נתונים":
    st.header("✅ אימות נתונים")

    if not st.session_state.client_data:
        st.warning("יש להזין נתונים תחילה בשלב 'הזנת נתונים'")
    else:
        # Show current data summary
        st.subheader("סיכום נתונים שהוזנו")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**מוכרים:** {len(st.session_state.sellers)}")
            for i, s in enumerate(st.session_state.sellers):
                st.markdown(f"  {i+1}. {s.get('name', 'לא הוזן')} ({s.get('id', '')})")
        with col2:
            st.markdown(f"**קונים:** {len(st.session_state.buyers)}")
            for i, b in enumerate(st.session_state.buyers):
                st.markdown(f"  {i+1}. {b.get('name', 'לא הוזן')} ({b.get('id', '')})")

        st.markdown(f"**נכס:** {st.session_state.property_data.get('address', 'לא הוזן')}")
        st.markdown(f"**מחיר:** {st.session_state.transaction_data.get('price', 0):,} ₪")

        st.markdown("---")

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
        st.info("לאחר השלמת כל התיקונים, תוכל להעלות תבנית חוזה מותאמת אישית")

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
            # Add seller declaration notes
            clean_data["seller_declaration_notes"] = st.session_state.seller_notes
            clean_data["all_sellers"] = st.session_state.sellers
            clean_data["all_buyers"] = st.session_state.buyers

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
                "num_sellers": len(st.session_state.sellers),
                "num_buyers": len(st.session_state.buyers),
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
