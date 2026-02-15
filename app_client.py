"""
Real Estate Contract - CLIENT Portal (Hebrew RTL)
=================================================
This is the client-facing app for data entry and document upload.
Data is sent to the lawyer via email.
"""

import os
import sys
import json
import streamlit as st
from pathlib import Path
from datetime import date, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from email_service import send_notification_email
from drive_service import create_transaction_folder, upload_json, upload_bytes
from template_filler import fill_template
import io

# Page config
st.set_page_config(
    page_title="טופס פרטי עסקת נדל\"ן",
    page_icon="🏠",
    layout="wide",
)

# RTL CSS only (no JavaScript to avoid loading issues)
st.markdown("""
<style>
    .stApp { direction: rtl; }
    .main .block-container { direction: rtl; text-align: right; }
    .stMarkdown, .stMarkdown p { direction: rtl; text-align: right; }
    .stTextInput label, .stSelectbox label, .stDateInput label,
    .stNumberInput label, .stTextArea label { text-align: right; }
    .stTextInput input, .stNumberInput input, .stTextArea textarea { direction: rtl; text-align: right; }
    [data-testid="stHorizontalBlock"] { flex-direction: row-reverse; }
    h1, h2, h3 { text-align: center; }
    #MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

st.title("🏠 טופס פרטי עסקת נדל\"ן")
st.markdown("---")

# Sidebar navigation
st.sidebar.header("שלבים")
pages = ["📝 הזנת נתונים", "📄 העלאת מסמכים", "✉️ שליחה"]

if "current_page" not in st.session_state:
    st.session_state.current_page = 0

page = pages[st.session_state.current_page]
st.sidebar.markdown(f"**שלב נוכחי:** {page}")

for i, p in enumerate(pages):
    if i < st.session_state.current_page:
        st.sidebar.markdown(f"✅ {p}")
    elif i == st.session_state.current_page:
        st.sidebar.markdown(f"➡️ **{p}**")
    else:
        st.sidebar.markdown(f"⬜ {p}")

# Initialize session state
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
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {}

# Marital status
MARITAL_OPTIONS = ["", "רווק/ה", "נשוי/אה", "גרוש/ה", "אלמן/ה"]
MARITAL_MAP = {"": "", "רווק/ה": "single", "נשוי/אה": "married", "גרוש/ה": "divorced", "אלמן/ה": "widowed"}
MARITAL_MAP_REVERSE = {v: k for k, v in MARITAL_MAP.items()}


def render_person_form(person_type: str, index: int, data: dict) -> dict:
    """Render form fields for a person."""
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


def go_next():
    st.session_state.current_page = min(st.session_state.current_page + 1, len(pages) - 1)

def go_back():
    st.session_state.current_page = max(st.session_state.current_page - 1, 0)


# ============ PAGE 1: DATA ENTRY ============
if page == "📝 הזנת נתונים":
    st.header("📝 הזנת פרטי העסקה")

    # SELLERS
    st.subheader("פרטי המוכרים")
    for i in range(len(st.session_state.sellers)):
        with st.expander(f"מוכר {i + 1}" + (f" - {st.session_state.sellers[i].get('name', '')}" if st.session_state.sellers[i].get('name') else ""), expanded=(i == 0)):
            st.session_state.sellers[i] = render_person_form("seller", i, st.session_state.sellers[i])
            if len(st.session_state.sellers) > 1:
                if st.button(f"🗑️ הסר מוכר {i + 1}", key=f"remove_seller_{i}"):
                    st.session_state.sellers.pop(i)
                    st.rerun()

    if st.button("➕ הוסף מוכר נוסף", key="add_seller"):
        st.session_state.sellers.append({"name": "", "id": "", "address": "", "phone": "", "email": "", "marital_status": ""})
        st.rerun()

    st.markdown("---")

    # BUYERS
    st.subheader("פרטי הקונים")
    for i in range(len(st.session_state.buyers)):
        with st.expander(f"קונה {i + 1}" + (f" - {st.session_state.buyers[i].get('name', '')}" if st.session_state.buyers[i].get('name') else ""), expanded=(i == 0)):
            st.session_state.buyers[i] = render_person_form("buyer", i, st.session_state.buyers[i])
            if len(st.session_state.buyers) > 1:
                if st.button(f"🗑️ הסר קונה {i + 1}", key=f"remove_buyer_{i}"):
                    st.session_state.buyers.pop(i)
                    st.rerun()

    if st.button("➕ הוסף קונה נוסף", key="add_buyer"):
        st.session_state.buyers.append({"name": "", "id": "", "address": "", "phone": "", "email": "", "marital_status": ""})
        st.rerun()

    col_bl1, col_bl2 = st.columns(2)
    with col_bl1:
        st.session_state.transaction_data["buyer_lawyer_email"] = st.text_input(
            "מייל עו\"ד הקונה",
            value=st.session_state.transaction_data.get("buyer_lawyer_email", ""),
            key="buyer_lawyer_email_input",
            placeholder="lawyer@example.com",
        )
    with col_bl2:
        st.session_state.transaction_data["buyer_lawyer"] = st.text_input(
            "שם עו\"ד הקונה",
            value=st.session_state.transaction_data.get("buyer_lawyer", ""),
            key="buyer_lawyer_input",
            placeholder="שם עורך הדין של הקונה",
        )

    st.markdown("---")

    # PROPERTY
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

    # TRANSACTION
    st.subheader("פרטי העסקה")
    trans = st.session_state.transaction_data
    col7, col8 = st.columns(2)
    with col7:
        trans["price"] = st.number_input("מחיר (₪) *", min_value=50000, max_value=100000000, value=int(trans.get("price", 1500000)), step=50000, key="price_input")
        default_sign = date.today() + timedelta(days=7)
        if trans.get("signing_date"):
            try: default_sign = date.fromisoformat(trans["signing_date"])
            except: pass
        trans["signing_date"] = st.date_input("תאריך חתימה *", value=default_sign, key="sign_date").strftime("%Y-%m-%d")
    with col8:
        default_del = date.today() + timedelta(days=90)
        if trans.get("delivery_date"):
            try: default_del = date.fromisoformat(trans["delivery_date"])
            except: pass
        trans["delivery_date"] = st.date_input("תאריך מסירה *", value=default_del, key="del_date").strftime("%Y-%m-%d")

    trans["mortgage_bank"] = st.text_input("בנק משכנתא", value=trans.get("mortgage_bank", ""), placeholder="לדוגמה: בנק לאומי", key="mortgage_bank_input")

    st.session_state.transaction_data = trans

    # Display calculated payment schedule (read-only)
    price = trans.get("price", 0)
    if price > 0:
        st.markdown("---")
        st.subheader("לוח תשלומים (חישוב אוטומטי)")
        payment_1 = int(price * 0.10)  # 10%
        payment_2 = int(price * 0.45)  # 45%
        payment_3 = int(price * 0.45)  # 45%
        escrow_amount = int(price * 0.15)  # 15% of total

        col_pay1, col_pay2, col_pay3 = st.columns(3)
        with col_pay1:
            st.metric("תשלום ראשון (10%)", f"₪{payment_1:,}")
        with col_pay2:
            st.metric("תשלום שני (45%)", f"₪{payment_2:,}")
        with col_pay3:
            st.metric("תשלום אחרון (45%)", f"₪{payment_3:,}")

        st.info(f"💰 סכום נאמנות (15% מסך העסקה): ₪{escrow_amount:,}")

    st.markdown("---")

    # SELLER NOTES
    st.subheader("הערות המוכר")
    st.session_state.seller_notes = st.text_area(
        "הערות נוספות של המוכר לגבי הנכס",
        value=st.session_state.seller_notes,
        key="seller_notes_input",
        height=150
    )

    st.markdown("---")

    # NAVIGATION
    col_nav1, col_nav2 = st.columns([1, 1])
    with col_nav2:
        if st.button("המשך ➡️", type="primary", key="next_1", use_container_width=True):
            go_next()
            st.rerun()


# ============ PAGE 2: DOCUMENT UPLOAD ============
elif page == "📄 העלאת מסמכים":
    st.header("📄 העלאת מסמכים")
    st.markdown("ניתן לגרור קבצים לאזור ההעלאה או ללחוץ לבחירה")

    st.markdown("---")

    # REQUIRED DOCUMENTS
    st.subheader("📋 מסמכים נדרשים")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**תעודות זהות מוכרים**")
        seller_ids = st.file_uploader("העלה ת.ז. מוכרים", type=None, accept_multiple_files=True, key="seller_ids")
        if seller_ids:
            st.session_state.uploaded_files["seller_ids"] = seller_ids

    with col2:
        st.markdown("**תעודות זהות קונים**")
        buyer_ids = st.file_uploader("העלה ת.ז. קונים", type=None, accept_multiple_files=True, key="buyer_ids")
        if buyer_ids:
            st.session_state.uploaded_files["buyer_ids"] = buyer_ids

    st.markdown("---")

    # PROPERTY DOCUMENTS
    st.subheader("🏠 מסמכי נכס")
    col3, col4 = st.columns(2)

    with col3:
        st.markdown("**נסח טאבו**")
        tabu = st.file_uploader("נסח רישום מקרקעין", type=None, key="tabu")
        if tabu:
            st.session_state.uploaded_files["tabu"] = tabu

    with col4:
        st.markdown("**מסמכי משכנתא**")
        mortgage_docs = st.file_uploader("מסמכי משכנתא", type=None, accept_multiple_files=True, key="mortgage")
        if mortgage_docs:
            st.session_state.uploaded_files["mortgage"] = mortgage_docs

    col5, col6 = st.columns(2)

    with col5:
        st.markdown("**אישור ארנונה**")
        arnona = st.file_uploader("אישור תשלום ארנונה", type=None, key="arnona")
        if arnona:
            st.session_state.uploaded_files["arnona"] = arnona

    with col6:
        st.markdown("**חוזה רכישה קודם (אופציונלי)**")
        purchase = st.file_uploader("חוזה רכישה מקורי", type=None, key="purchase")
        if purchase:
            st.session_state.uploaded_files["purchase"] = purchase

    st.markdown("---")

    # OTHER DOCUMENTS
    st.subheader("📎 מסמכים נוספים")
    other = st.file_uploader("העלה מסמכים נוספים", type=None, accept_multiple_files=True, key="other")
    if other:
        st.session_state.uploaded_files["other"] = other

    # Show summary
    st.markdown("---")
    st.subheader("סיכום מסמכים")
    files = st.session_state.uploaded_files
    if files.get("seller_ids"): st.markdown(f"✅ תעודות זהות מוכרים: {len(files['seller_ids'])}")
    if files.get("buyer_ids"): st.markdown(f"✅ תעודות זהות קונים: {len(files['buyer_ids'])}")
    if files.get("tabu"): st.markdown("✅ נסח טאבו")
    if files.get("mortgage"): st.markdown(f"✅ מסמכי משכנתא: {len(files['mortgage'])}")
    if files.get("arnona"): st.markdown("✅ אישור ארנונה")
    if files.get("purchase"): st.markdown("✅ חוזה רכישה קודם")
    if files.get("other"): st.markdown(f"✅ מסמכים נוספים: {len(files['other'])}")

    st.markdown("---")

    # NAVIGATION
    col_nav1, col_nav2 = st.columns([1, 1])
    with col_nav1:
        if st.button("⬅️ חזור", key="back_2", use_container_width=True):
            go_back()
            st.rerun()
    with col_nav2:
        if st.button("המשך ➡️", type="primary", key="next_2", use_container_width=True):
            go_next()
            st.rerun()


# ============ PAGE 3: SEND ============
elif page == "✉️ שליחה":
    st.header("✉️ שליחת הנתונים לעורך הדין")

    # Summary
    st.subheader("סיכום העסקה")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**מוכרים:** {len(st.session_state.sellers)}")
        for i, s in enumerate(st.session_state.sellers):
            st.markdown(f"  {i+1}. {s.get('name', 'לא הוזן')}")
    with col2:
        st.markdown(f"**קונים:** {len(st.session_state.buyers)}")
        for i, b in enumerate(st.session_state.buyers):
            st.markdown(f"  {i+1}. {b.get('name', 'לא הוזן')}")

    st.markdown(f"**נכס:** {st.session_state.property_data.get('address', 'לא הוזן')}")
    st.markdown(f"**מחיר:** {st.session_state.transaction_data.get('price', 0):,} ₪")

    files_count = sum(1 for v in st.session_state.uploaded_files.values() if v)
    st.markdown(f"**מסמכים:** {files_count} סוגי קבצים הועלו")

    st.markdown("---")

    # Email config (should be in .env in production)
    st.info("לחץ על 'שלח' כדי להעביר את כל הנתונים לעורך הדין")

    st.markdown("---")

    # NAVIGATION
    col_nav1, col_nav2 = st.columns([1, 1])
    with col_nav1:
        if st.button("⬅️ חזור", key="back_3", use_container_width=True):
            go_back()
            st.rerun()
    with col_nav2:
        if st.button("📤 שלח לעורך הדין", type="primary", key="send", use_container_width=True):
            progress = st.progress(0)
            status = st.empty()

            try:
                seller_name = st.session_state.sellers[0].get("name", "לא ידוע")
                property_address = st.session_state.property_data.get("address", "לא ידוע")

                # Step 1: Prepare data
                status.text("מכין נתונים...")
                progress.progress(10)

                data = {
                    "sellers": st.session_state.sellers,
                    "buyers": st.session_state.buyers,
                    "property": st.session_state.property_data,
                    "transaction": st.session_state.transaction_data,
                    "seller_notes": st.session_state.seller_notes,
                }

                # Step 2: Create folder in Google Drive by property address
                status.text("יוצר תיקייה בגוגל דרייב...")
                progress.progress(20)

                folder_info = create_transaction_folder(property_address)
                folder_id = folder_info["folder_id"]
                folder_link = folder_info["folder_link"]

                # Step 3: Upload JSON data to Google Drive
                status.text("מעלה נתונים לגוגל דרייב...")
                progress.progress(40)

                upload_json(data, "transaction_data.json", folder_id)

                # Step 4: Upload all files to the same folder
                status.text("מעלה מסמכים לגוגל דרייב...")
                progress.progress(60)

                files_uploaded = 0
                for doc_type, files in st.session_state.uploaded_files.items():
                    if files:
                        if isinstance(files, list):
                            for i, f in enumerate(files):
                                f.seek(0)
                                file_name = f"{doc_type}_{i+1}_{f.name}"
                                upload_bytes(f.read(), file_name, folder_id)
                                files_uploaded += 1
                        else:
                            files.seek(0)
                            file_name = f"{doc_type}_{files.name}"
                            upload_bytes(files.read(), file_name, folder_id)
                            files_uploaded += 1

                # Step 5: Generate contract from template
                status.text("מייצר חוזה מתבנית...")
                progress.progress(70)

                # Fill template with transaction data
                doc = fill_template(data)

                # Save to bytes buffer
                contract_buffer = io.BytesIO()
                doc.save(contract_buffer)
                contract_buffer.seek(0)

                # Upload contract to Google Drive
                status.text("מעלה חוזה לגוגל דרייב...")
                progress.progress(85)

                contract_filename = f"חוזה_מכר_{property_address.replace(' ', '_')}.docx"
                upload_bytes(contract_buffer.read(), contract_filename, folder_id)

                # Step 6: Send email notification
                status.text("שולח התראה לעורך הדין...")
                progress.progress(95)

                email_result = send_notification_email(
                    seller_name=seller_name,
                    property_address=property_address,
                    drive_folder_link=folder_link
                )

                progress.progress(100)
                status.text("הושלם!")

                st.success("✅ הנתונים נשלחו בהצלחה!")
                st.balloons()

                st.markdown("---")
                st.markdown("### סיכום:")
                st.markdown(f"📁 **תיקייה בגוגל דרייב:** [{folder_info['folder_name']}]({folder_link})")
                st.markdown(f"📄 **חוזה נוצר:** {contract_filename}")
                st.markdown(f"📎 **מסמכים שהועלו:** {files_uploaded}")
                st.markdown(f"📧 **התראה לעורך הדין:** {email_result.get('message', 'נשלחה')}")

                st.markdown("---")
                st.markdown("### מה קורה עכשיו?")
                st.markdown("החוזה נוצר אוטומטית והועלה לתיקייה. עורך הדין יקבל התראה ויבדוק את החוזה.")

            except Exception as e:
                st.error(f"❌ שגיאה: {str(e)}")
                st.info("נסה שוב או פנה לתמיכה")
