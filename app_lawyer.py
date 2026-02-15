"""
Real Estate Contract - LAWYER Portal (Hebrew RTL)
=================================================
This is the lawyer-facing app for reviewing data and generating contracts.
"""

import os
import sys
import json
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from crews.crew1_data.tools.data_cleaner import merge_and_clean
from crews.crew2_contract.tools.contract_builder import build_contract_document
from crews.crew2_contract.tools.legal_compliance import run_compliance_check

# Page config
st.set_page_config(
    page_title="מערכת יצירת חוזים - עורך דין",
    page_icon="⚖️",
    layout="wide",
)

# RTL CSS
st.markdown("""
<style>
    .stApp { direction: rtl; }
    .stMarkdown, .stText, label, .stSelectbox, .stTextInput, .stNumberInput { direction: rtl; text-align: right; }
    h1, h2, h3 { text-align: center; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
<script>
    window.scrollTo(0, 0);
</script>
""", unsafe_allow_html=True)

st.title("⚖️ מערכת יצירת חוזים")
st.markdown("---")

# Sidebar
st.sidebar.header("ניווט")
pages = ["📂 בחירת עסקה", "👀 סקירת נתונים", "📝 יצירת חוזה"]

if "lawyer_page" not in st.session_state:
    st.session_state.lawyer_page = 0
if "selected_transaction" not in st.session_state:
    st.session_state.selected_transaction = None
if "transaction_data" not in st.session_state:
    st.session_state.transaction_data = None

page = pages[st.session_state.lawyer_page]

for i, p in enumerate(pages):
    if i < st.session_state.lawyer_page:
        st.sidebar.markdown(f"✅ {p}")
    elif i == st.session_state.lawyer_page:
        st.sidebar.markdown(f"➡️ **{p}**")
    else:
        st.sidebar.markdown(f"⬜ {p}")


def go_next():
    st.session_state.lawyer_page = min(st.session_state.lawyer_page + 1, len(pages) - 1)

def go_back():
    st.session_state.lawyer_page = max(st.session_state.lawyer_page - 1, 0)


# ============ PAGE 1: SELECT TRANSACTION ============
if page == "📂 בחירת עסקה":
    st.header("📂 בחירת עסקה")

    submissions_dir = Path("submissions")
    if not submissions_dir.exists():
        st.warning("אין עסקאות במערכת")
    else:
        # Find all transaction files
        transactions = list(submissions_dir.glob("transaction_*.json"))

        if not transactions:
            st.warning("אין עסקאות במערכת")
        else:
            st.subheader("עסקאות זמינות")

            for tx_file in sorted(transactions, reverse=True):
                with open(tx_file, "r", encoding="utf-8") as f:
                    tx_data = json.load(f)

                seller_name = tx_data["sellers"][0]["name"] if tx_data.get("sellers") else "לא ידוע"
                buyer_name = tx_data["buyers"][0]["name"] if tx_data.get("buyers") else "לא ידוע"
                property_addr = tx_data.get("property", {}).get("address", "לא ידוע")
                price = tx_data.get("transaction", {}).get("price", 0)

                with st.expander(f"🏠 {property_addr} | {seller_name} → {buyer_name}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**מוכרים:** {len(tx_data.get('sellers', []))}")
                        st.markdown(f"**קונים:** {len(tx_data.get('buyers', []))}")
                    with col2:
                        st.markdown(f"**מחיר:** {price:,} ₪")
                        st.markdown(f"**קובץ:** {tx_file.name}")

                    # Check for files
                    files_dir = tx_file.parent / tx_file.name.replace("transaction_", "files_").replace(".json", "")
                    if files_dir.exists():
                        files_count = len(list(files_dir.glob("*")))
                        st.markdown(f"**מסמכים:** {files_count} קבצים")

                    if st.button("בחר עסקה זו", key=f"select_{tx_file.name}"):
                        st.session_state.selected_transaction = str(tx_file)
                        st.session_state.transaction_data = tx_data
                        go_next()
                        st.rerun()

    st.markdown("---")


# ============ PAGE 2: REVIEW DATA ============
elif page == "👀 סקירת נתונים":
    st.header("👀 סקירת נתונים")

    if not st.session_state.transaction_data:
        st.warning("יש לבחור עסקה תחילה")
        if st.button("⬅️ חזור לבחירת עסקה"):
            go_back()
            st.rerun()
    else:
        tx = st.session_state.transaction_data

        # SELLERS
        st.subheader("מוכרים")
        for i, seller in enumerate(tx.get("sellers", [])):
            with st.expander(f"מוכר {i+1}: {seller.get('name', '')}", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**שם:** {seller.get('name', '')}")
                    st.markdown(f"**ת.ז.:** {seller.get('id', '')}")
                    st.markdown(f"**כתובת:** {seller.get('address', '')}")
                with col2:
                    st.markdown(f"**טלפון:** {seller.get('phone', '')}")
                    st.markdown(f"**אימייל:** {seller.get('email', '')}")
                    marital = {"": "", "single": "רווק/ה", "married": "נשוי/אה", "divorced": "גרוש/ה", "widowed": "אלמן/ה"}
                    st.markdown(f"**מצב משפחתי:** {marital.get(seller.get('marital_status', ''), '')}")

        # BUYERS
        st.subheader("קונים")
        for i, buyer in enumerate(tx.get("buyers", [])):
            with st.expander(f"קונה {i+1}: {buyer.get('name', '')}", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**שם:** {buyer.get('name', '')}")
                    st.markdown(f"**ת.ז.:** {buyer.get('id', '')}")
                    st.markdown(f"**כתובת:** {buyer.get('address', '')}")
                with col2:
                    st.markdown(f"**טלפון:** {buyer.get('phone', '')}")
                    st.markdown(f"**אימייל:** {buyer.get('email', '')}")
                    st.markdown(f"**מצב משפחתי:** {marital.get(buyer.get('marital_status', ''), '')}")

        if tx.get("buyer_lawyer") or tx.get("buyer_lawyer_email"):
            col_bl1, col_bl2 = st.columns(2)
            with col_bl1:
                st.markdown(f"**עו\"ד הקונה:** {tx.get('buyer_lawyer', '')}")
            with col_bl2:
                st.markdown(f"**מייל עו\"ד הקונה:** {tx.get('buyer_lawyer_email', '')}")

        # PROPERTY
        st.subheader("פרטי הנכס")
        prop = tx.get("property", {})
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**כתובת:** {prop.get('address', '')}")
            st.markdown(f"**גוש:** {prop.get('block_number', '')} | **חלקה:** {prop.get('parcel_number', '')} | **תת-חלקה:** {prop.get('sub_parcel', '')}")
            st.markdown(f"**שטח:** {prop.get('area_sqm', '')} מ\"ר | **חדרים:** {prop.get('rooms', '')}")
        with col2:
            types = {"apartment": "דירה", "penthouse": "פנטהאוז", "garden": "דירת גן", "duplex": "דופלקס", "house": "בית פרטי", "land": "מגרש"}
            st.markdown(f"**סוג:** {types.get(prop.get('property_type', ''), '')}")
            st.markdown(f"**קומה:** {prop.get('floor', '')}")
            parking = {"none": "ללא", "covered": "מקורה", "uncovered": "לא מקורה", "underground": "תת-קרקעית"}
            st.markdown(f"**חניה:** {parking.get(prop.get('parking', ''), '')} | **מחסן:** {'כן' if prop.get('storage') == 'yes' else 'לא'}")

        # TRANSACTION
        st.subheader("פרטי העסקה")
        trans = tx.get("transaction", {})
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**מחיר:** {trans.get('price', 0):,} ₪")
        with col2:
            st.markdown(f"**חתימה:** {trans.get('signing_date', '')} | **מסירה:** {trans.get('delivery_date', '')}")

        # SELLER NOTES
        if tx.get("seller_notes"):
            st.subheader("הערות המוכר")
            st.info(tx["seller_notes"])

        # DOCUMENTS
        tx_file = Path(st.session_state.selected_transaction)
        files_dir = tx_file.parent / tx_file.name.replace("transaction_", "files_").replace(".json", "")
        if files_dir.exists():
            st.subheader("מסמכים")
            for f in files_dir.glob("*"):
                st.markdown(f"📎 {f.name}")

        st.markdown("---")

        # NAVIGATION
        col_nav1, col_nav2 = st.columns([1, 1])
        with col_nav1:
            if st.button("⬅️ חזור", key="back_review", use_container_width=True):
                go_back()
                st.rerun()
        with col_nav2:
            if st.button("המשך ליצירת חוזה ➡️", type="primary", key="next_review", use_container_width=True):
                go_next()
                st.rerun()


# ============ PAGE 3: GENERATE CONTRACT ============
elif page == "📝 יצירת חוזה":
    st.header("📝 יצירת חוזה")

    if not st.session_state.transaction_data:
        st.warning("יש לבחור עסקה תחילה")
        if st.button("⬅️ חזור"):
            st.session_state.lawyer_page = 0
            st.rerun()
    else:
        tx = st.session_state.transaction_data

        st.info("לחץ על הכפתור ליצירת החוזה")

        if st.button("🔨 צור חוזה", type="primary", use_container_width=True):
            progress = st.progress(0)
            status = st.empty()

            status.text("מכין נתונים...")
            progress.progress(20)

            # Convert to clean_data format
            sellers = tx.get("sellers", [])
            buyers = tx.get("buyers", [])
            primary_seller = sellers[0] if sellers else {}
            secondary_seller = sellers[1] if len(sellers) > 1 else {}
            primary_buyer = buyers[0] if buyers else {}
            secondary_buyer = buyers[1] if len(buyers) > 1 else {}
            prop = tx.get("property", {})
            trans = tx.get("transaction", {})

            # Calculate payment schedule
            price_val = trans.get("price", 0)
            payment_1 = int(price_val * 0.10)  # 10%
            payment_2 = int(price_val * 0.45)  # 45%
            payment_3 = int(price_val * 0.45)  # 45%
            escrow_amount = int(price_val * 0.15)  # 15% of total

            client_data = {
                "seller_name": primary_seller.get("name", ""),
                "seller_id": primary_seller.get("id", ""),
                "seller_address": primary_seller.get("address", ""),
                "seller_phone": primary_seller.get("phone", ""),
                "seller_email": primary_seller.get("email", ""),
                "seller_marital_status": primary_seller.get("marital_status", ""),
                "seller2_name": secondary_seller.get("name", ""),
                "seller2_id": secondary_seller.get("id", ""),
                "buyer_name": primary_buyer.get("name", ""),
                "buyer_id": primary_buyer.get("id", ""),
                "buyer_address": primary_buyer.get("address", ""),
                "buyer_phone": primary_buyer.get("phone", ""),
                "buyer_email": primary_buyer.get("email", ""),
                "buyer_marital_status": primary_buyer.get("marital_status", ""),
                "buyer2_name": secondary_buyer.get("name", ""),
                "buyer2_id": secondary_buyer.get("id", ""),
                "buyer_lawyer": trans.get("buyer_lawyer", ""),
                "buyer_lawyer_email": trans.get("buyer_lawyer_email", ""),
                "mortgage_bank": trans.get("mortgage_bank", ""),
                "property_address": prop.get("address", ""),
                "block_number": prop.get("block_number", ""),
                "parcel_number": prop.get("parcel_number", ""),
                "sub_parcel": prop.get("sub_parcel", ""),
                "area_sqm": str(prop.get("area_sqm", "")),
                "rooms": str(prop.get("rooms", "")),
                "floor": str(prop.get("floor", "")),
                "property_type": prop.get("property_type", "apartment"),
                "parking": prop.get("parking", "none"),
                "storage": prop.get("storage", "no"),
                "price": str(trans.get("price", "")),
                "payment_1": payment_1,
                "payment_2": payment_2,
                "payment_3": payment_3,
                "escrow_amount": escrow_amount,
                "signing_date": trans.get("signing_date", ""),
                "delivery_date": trans.get("delivery_date", ""),
                "notes": tx.get("seller_notes", ""),
                "seller_declaration_notes": tx.get("seller_notes", ""),
                "all_sellers": sellers,
                "all_buyers": buyers,
            }

            status.text("מנקה ומעבד נתונים...")
            progress.progress(40)
            clean_data = merge_and_clean(client_data, None)
            clean_data["seller_declaration_notes"] = tx.get("seller_notes", "")
            clean_data["all_sellers"] = tx.get("sellers", [])
            clean_data["all_buyers"] = tx.get("buyers", [])

            status.text("בודק תאימות משפטית...")
            progress.progress(60)
            compliance = run_compliance_check(clean_data)

            status.text("יוצר חוזה...")
            progress.progress(80)
            os.makedirs("contracts", exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            seller_name = primary_seller.get("name", "unknown").replace(" ", "_")
            contract_filename = f"contracts/contract_{seller_name}_{timestamp}.docx"

            doc = build_contract_document(clean_data, "standard")
            doc.save(contract_filename)

            status.text("הושלם!")
            progress.progress(100)

            st.success("✅ החוזה נוצר בהצלחה!")

            # Download button
            with open(contract_filename, "rb") as f:
                st.download_button(
                    label="📥 הורד חוזה",
                    data=f.read(),
                    file_name=f"contract_{seller_name}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )

            st.info(f"📁 החוזה נשמר: {contract_filename}")

            # Show compliance summary
            if compliance.get("compliant"):
                st.success(f"✅ תאימות משפטית: {compliance.get('passed', 0)}/{compliance.get('total_checks', 0)} בדיקות עברו")
            else:
                st.warning(f"⚠️ יש בעיות תאימות - בדוק את החוזה")

        st.markdown("---")

        # NAVIGATION
        if st.button("⬅️ חזור לסקירה", key="back_contract", use_container_width=True):
            go_back()
            st.rerun()
