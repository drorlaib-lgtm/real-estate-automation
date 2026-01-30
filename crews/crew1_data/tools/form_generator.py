"""Form Generator Tool - Creates Hebrew RTL HTML forms for client data collection."""

import os
from crewai.tools import tool


FORM_TEMPLATE = """<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>טופס פרטי עסקת נדל"ן</title>
    <style>
        * {{ box-sizing: border-box; font-family: 'Segoe UI', Tahoma, sans-serif; }}
        body {{ background: #f5f5f5; padding: 20px; direction: rtl; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #1a237e; text-align: center; }}
        h2 {{ color: #283593; border-bottom: 2px solid #3f51b5; padding-bottom: 8px; }}
        .form-group {{ margin-bottom: 15px; }}
        label {{ display: block; margin-bottom: 5px; font-weight: bold; color: #333; }}
        input, select, textarea {{ width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; font-size: 14px; }}
        input:focus, select:focus, textarea:focus {{ border-color: #3f51b5; outline: none; }}
        .required::after {{ content: " *"; color: red; }}
        .btn {{ background: #3f51b5; color: white; padding: 12px 30px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }}
        .btn:hover {{ background: #283593; }}
        .section {{ margin-bottom: 30px; }}
    </style>
</head>
<body>
<div class="container">
    <h1>🏠 טופס פרטי עסקת נדל"ן</h1>
    <form id="realEstateForm" method="POST">

        <div class="section">
            <h2>פרטי המוכר</h2>
            <div class="form-group">
                <label class="required">שם מלא</label>
                <input type="text" name="seller_name" required>
            </div>
            <div class="form-group">
                <label class="required">תעודת זהות</label>
                <input type="text" name="seller_id" pattern="[0-9]{{5,9}}" required>
            </div>
            <div class="form-group">
                <label class="required">כתובת מגורים</label>
                <input type="text" name="seller_address" required>
            </div>
            <div class="form-group">
                <label class="required">טלפון</label>
                <input type="tel" name="seller_phone" pattern="0[0-9]{{8,9}}" required>
            </div>
            <div class="form-group">
                <label class="required">דוא"ל</label>
                <input type="email" name="seller_email" required>
            </div>
            <div class="form-group">
                <label>מצב משפחתי</label>
                <select name="seller_marital_status">
                    <option value="">בחר...</option>
                    <option value="single">רווק/ה</option>
                    <option value="married">נשוי/אה</option>
                    <option value="divorced">גרוש/ה</option>
                    <option value="widowed">אלמן/ה</option>
                </select>
            </div>
        </div>

        <div class="section">
            <h2>פרטי הקונה</h2>
            <div class="form-group">
                <label class="required">שם מלא</label>
                <input type="text" name="buyer_name" required>
            </div>
            <div class="form-group">
                <label class="required">תעודת זהות</label>
                <input type="text" name="buyer_id" pattern="[0-9]{{5,9}}" required>
            </div>
            <div class="form-group">
                <label class="required">כתובת מגורים</label>
                <input type="text" name="buyer_address" required>
            </div>
            <div class="form-group">
                <label class="required">טלפון</label>
                <input type="tel" name="buyer_phone" pattern="0[0-9]{{8,9}}" required>
            </div>
            <div class="form-group">
                <label class="required">דוא"ל</label>
                <input type="email" name="buyer_email" required>
            </div>
        </div>

        <div class="section">
            <h2>פרטי הנכס</h2>
            <div class="form-group">
                <label class="required">כתובת הנכס</label>
                <input type="text" name="property_address" required>
            </div>
            <div class="form-group">
                <label class="required">גוש</label>
                <input type="text" name="block_number" required>
            </div>
            <div class="form-group">
                <label class="required">חלקה</label>
                <input type="text" name="parcel_number" required>
            </div>
            <div class="form-group">
                <label>תת-חלקה</label>
                <input type="text" name="sub_parcel">
            </div>
            <div class="form-group">
                <label class="required">שטח במ"ר</label>
                <input type="number" name="area_sqm" min="1" required>
            </div>
            <div class="form-group">
                <label class="required">מספר חדרים</label>
                <input type="number" name="rooms" min="1" step="0.5" required>
            </div>
            <div class="form-group">
                <label>קומה</label>
                <input type="number" name="floor" min="-2">
            </div>
            <div class="form-group">
                <label class="required">סוג הנכס</label>
                <select name="property_type" required>
                    <option value="">בחר...</option>
                    <option value="apartment">דירה</option>
                    <option value="penthouse">פנטהאוז</option>
                    <option value="garden">דירת גן</option>
                    <option value="duplex">דופלקס</option>
                    <option value="house">בית פרטי</option>
                    <option value="land">מגרש</option>
                </select>
            </div>
            <div class="form-group">
                <label>חניה</label>
                <select name="parking">
                    <option value="none">ללא</option>
                    <option value="covered">מקורה</option>
                    <option value="uncovered">לא מקורה</option>
                    <option value="underground">תת-קרקעית</option>
                </select>
            </div>
            <div class="form-group">
                <label>מחסן</label>
                <select name="storage">
                    <option value="no">לא</option>
                    <option value="yes">כן</option>
                </select>
            </div>
        </div>

        <div class="section">
            <h2>פרטי העסקה</h2>
            <div class="form-group">
                <label class="required">מחיר העסקה (₪)</label>
                <input type="number" name="price" min="1" required>
            </div>
            <div class="form-group">
                <label class="required">תאריך חתימה משוער</label>
                <input type="date" name="signing_date" required>
            </div>
            <div class="form-group">
                <label class="required">תאריך מסירת חזקה</label>
                <input type="date" name="delivery_date" required>
            </div>
            <div class="form-group">
                <label>הערות נוספות</label>
                <textarea name="notes" rows="4"></textarea>
            </div>
        </div>

        <div class="form-group" style="text-align: center;">
            <button type="submit" class="btn">שלח טופס</button>
        </div>
    </form>
</div>

<script>
document.getElementById('realEstateForm').addEventListener('submit', function(e) {{
    e.preventDefault();
    const formData = new FormData(this);
    const data = Object.fromEntries(formData.entries());
    console.log('Form Data:', JSON.stringify(data, null, 2));
    alert('הטופס נשלח בהצלחה!');
}});
</script>
</body>
</html>"""


@tool("generate_client_form")
def generate_client_form(output_path: str = "artifacts/client_form.html") -> str:
    """Generate an HTML form for real estate client data collection in Hebrew RTL.
    Returns the path to the generated HTML form file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(FORM_TEMPLATE)
    return f"טופס HTML נוצר בהצלחה: {output_path}"
