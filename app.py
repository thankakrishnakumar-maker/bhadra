import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import uuid
import base64
import time
import json
import io
import urllib.parse

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="🛕 Sree Bhadreshwari Amman Temple",
    page_icon="🛕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# SUPABASE CONNECTION
# ============================================================
try:
    from supabase import create_client, Client
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

    @st.cache_resource
    def get_supabase_client():
        return create_client(SUPABASE_URL, SUPABASE_KEY)

    supabase: Client = get_supabase_client()
    DB_CONNECTED = True
except Exception as e:
    DB_CONNECTED = False
    st.error(f"Database connection failed: {str(e)}")

# ============================================================
# PDF GENERATION
# ============================================================
try:
    from fpdf import FPDF

    class BillPDF(FPDF):
        def header(self):
            self.set_font('Helvetica', 'B', 16)
            self.cell(0, 10, 'Sree Bhadreshwari Amman Temple', 0, 1, 'C')
            self.set_font('Helvetica', '', 10)
            self.cell(0, 6, 'Amme Narayana .. Devi Narayana', 0, 1, 'C')
            self.line(10, self.get_y() + 2, 200, self.get_y() + 2)
            self.ln(5)

        def footer(self):
            self.set_y(-25)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(3)
            self.set_font('Helvetica', 'I', 8)
            self.cell(0, 5, 'Thank you for your contribution! May Goddess bless you!', 0, 1, 'C')
            self.cell(0, 5, 'Amme Narayana .. Devi Narayana', 0, 1, 'C')

    def generate_bill_pdf(bill_no, manual_bill, bill_book, bill_date,
                          name, address, mobile, pooja_type, amount):
        pdf = BillPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=30)

        # Bill details box
        pdf.set_font('Helvetica', '', 10)
        pdf.set_fill_color(255, 248, 240)

        y_start = pdf.get_y()
        pdf.rect(10, y_start, 190, 85, 'D')

        pdf.set_xy(15, y_start + 5)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(0, 7, 'BILL / RECEIPT', 0, 1, 'C')
        pdf.ln(3)

        details = [
            ("Bill No", str(bill_no)),
            ("Manual Bill No", str(manual_bill)),
            ("Bill Book No", str(bill_book)),
            ("Date", str(bill_date)),
        ]
        pdf.set_font('Helvetica', '', 10)
        for label, value in details:
            pdf.set_x(15)
            pdf.set_font('Helvetica', 'B', 10)
            pdf.cell(45, 7, f"{label}:", 0, 0)
            pdf.set_font('Helvetica', '', 10)
            pdf.cell(0, 7, value, 0, 1)

        pdf.ln(2)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(3)

        devotee_details = [
            ("Name", str(name)),
            ("Address", str(address)),
            ("Mobile", str(mobile)),
        ]
        for label, value in devotee_details:
            pdf.set_x(15)
            pdf.set_font('Helvetica', 'B', 10)
            pdf.cell(45, 7, f"{label}:", 0, 0)
            pdf.set_font('Helvetica', '', 10)
            pdf.cell(0, 7, value, 0, 1)

        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

        # Pooja & Amount
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_x(15)
        pdf.cell(45, 8, "Pooja Type:", 0, 0)
        pdf.set_font('Helvetica', '', 11)
        pdf.cell(0, 8, str(pooja_type), 0, 1)

        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_x(15)
        pdf.cell(45, 10, "Amount:", 0, 0)
        pdf.set_text_color(0, 128, 0)
        pdf.cell(0, 10, f"Rs. {float(amount):,.2f}", 0, 1)
        pdf.set_text_color(0, 0, 0)

        return pdf.output()

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# ============================================================
# CONSTANTS
# ============================================================
NATCHATHIRAM_LIST = [
    "Ashwini", "Bharani", "Karthigai",
    "Rohini", "Mrigashirsha", "Thiruvadirai",
    "Punarvasu", "Pushya", "Ashlesha",
    "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati",
    "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha",
    "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

RELATION_TYPES = [
    "Self", "Spouse", "Son", "Daughter", "Father", "Mother",
    "Brother", "Sister", "Grandfather", "Grandmother",
    "Father-in-law", "Mother-in-law", "Son-in-law",
    "Daughter-in-law", "Uncle", "Aunt", "Nephew", "Niece", "Other"
]

MIN_DATE = date(1900, 1, 1)
MAX_DATE = date(2050, 12, 31)

# ============================================================
# CUSTOM CSS
# ============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    * { font-family: 'Poppins', sans-serif; }
    .main-header {
        background: linear-gradient(135deg, #ff6b35 0%, #f7c948 50%, #ff6b35 100%);
        padding: 20px; border-radius: 15px; text-align: center;
        margin-bottom: 20px; box-shadow: 0 4px 15px rgba(255,107,53,0.3);
    }
    .main-header h1 { color: #8B0000; font-size: 1.8em; margin: 0; }
    .main-header p { color: #5a1a00; font-size: 1em; margin: 5px 0 0 0; }
    .login-container {
        padding: 30px; border-radius: 20px; backdrop-filter: blur(10px);
        background: rgba(255,255,255,0.92); box-shadow: 0 8px 32px rgba(0,0,0,0.15);
        border: 1px solid rgba(255,107,53,0.2);
    }
    .amman-photo-container { text-align: center; margin-bottom: 15px; }
    .amman-photo {
        width: 130px; height: 130px; border-radius: 50%; object-fit: cover;
        border: 4px solid #ff6b35;
        box-shadow: 0 4px 20px rgba(255,107,53,0.4), 0 0 30px rgba(247,201,72,0.3);
        animation: glow 2s ease-in-out infinite alternate;
    }
    @keyframes glow {
        from { box-shadow: 0 4px 20px rgba(255,107,53,0.4), 0 0 30px rgba(247,201,72,0.3); }
        to { box-shadow: 0 4px 30px rgba(255,107,53,0.6), 0 0 50px rgba(247,201,72,0.5); }
    }
    .metric-card {
        padding: 20px; border-radius: 12px; color: white;
        text-align: center; margin: 5px; box-shadow: 0 4px 10px rgba(0,0,0,0.15);
    }
    .metric-card.income { background: linear-gradient(135deg, #11998e, #38ef7d); }
    .metric-card.expense { background: linear-gradient(135deg, #eb3349, #f45c43); }
    .metric-card.balance { background: linear-gradient(135deg, #4facfe, #00f2fe); }
    .metric-card.info { background: linear-gradient(135deg, #667eea, #764ba2); }
    .metric-card h3 { margin: 0; font-size: 0.85em; opacity: 0.9; }
    .metric-card h2 { margin: 5px 0 0 0; font-size: 1.7em; }
    .news-ticker-wrapper {
        background: linear-gradient(90deg, #1a1a2e, #16213e, #0f3460);
        padding: 12px 20px; border-radius: 10px; overflow: hidden;
        white-space: nowrap; margin: 10px 0;
    }
    .news-ticker-text {
        display: inline-block; color: #f7c948; font-size: 1em;
        animation: scroll-left 35s linear infinite;
    }
    @keyframes scroll-left {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-200%); }
    }
    .pooja-card {
        background: linear-gradient(135deg, #ffecd2, #fcb69f);
        padding: 12px 15px; border-radius: 10px; margin: 5px 0;
        border-left: 4px solid #ff6b35;
    }
    .birthday-card {
        background: linear-gradient(135deg, #a8edea, #fed6e3);
        padding: 10px 15px; border-radius: 10px; margin: 5px 0;
        border-left: 4px solid #e91e63;
    }
    .success-box {
        background: #d4edda; border: 1px solid #c3e6cb; padding: 15px;
        border-radius: 10px; color: #155724; margin: 10px 0;
    }
    .wa-btn {
        display: inline-block; background: #25D366; color: white !important;
        padding: 10px 25px; border-radius: 8px; text-decoration: none;
        font-weight: 600; font-size: 0.95em; margin: 5px;
        box-shadow: 0 3px 8px rgba(37,211,102,0.3);
    }
    .wa-btn:hover { background: #128C7E; color: white !important; }
    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    div[data-testid="stSidebar"] .stButton > button {
        width: 100%; text-align: left; background: transparent;
        color: #f0f0f0; border: 1px solid rgba(255,255,255,0.1);
        border-radius: 8px; margin: 2px 0; padding: 8px 15px;
    }
    div[data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255,107,53,0.3); border-color: #ff6b35;
    }
    .temple-name-login {
        color: #8B0000; font-size: 1.5em; font-weight: 700;
        text-align: center; margin: 10px 0;
    }
    .tamil-text {
        color: #c0392b; font-size: 1.1em; font-weight: 600;
        text-align: center; margin: 5px 0 15px 0;
    }
    .upload-result {
        background: #e8f5e9; border: 1px solid #a5d6a7; padding: 15px;
        border-radius: 10px; margin: 10px 0;
    }
    .upload-error {
        background: #ffebee; border: 1px solid #ef9a9a; padding: 15px;
        border-radius: 10px; margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE
# ============================================================
defaults = {
    'logged_in': False, 'username': '', 'user_role': '',
    'current_page': 'Dashboard', 'bg_image_base64': None,
    'amman_photo_base64': None, 'last_bill_pdf': None,
    'last_bill_wa_link': None, 'last_bill_info': None
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ============================================================
# DATABASE HELPERS
# ============================================================
def db_select(table, columns="*", filters=None, gte_filters=None, lte_filters=None):
    try:
        query = supabase.table(table).select(columns)
        if filters:
            for k, v in filters.items():
                query = query.eq(k, v)
        if gte_filters:
            for k, v in gte_filters.items():
                query = query.gte(k, str(v))
        if lte_filters:
            for k, v in lte_filters.items():
                query = query.lte(k, str(v))
        result = query.execute()
        return result.data if result.data else []
    except Exception as e:
        st.error(f"DB Error ({table}): {e}")
        return []

def db_insert(table, data):
    try:
        result = supabase.table(table).insert(data).execute()
        return result.data if result.data else None
    except Exception as e:
        st.error(f"Insert Error ({table}): {e}")
        return None

def db_update(table, data, col, val):
    try:
        result = supabase.table(table).update(data).eq(col, val).execute()
        return result.data
    except Exception as e:
        st.error(f"Update Error ({table}): {e}")
        return None

def db_delete(table, col, val):
    try:
        supabase.table(table).delete().eq(col, val).execute()
        return True
    except Exception as e:
        st.error(f"Delete Error ({table}): {e}")
        return False

def file_to_base64(f):
    if f:
        return f"data:{f.type};base64,{base64.b64encode(f.getvalue()).decode()}"
    return None

def get_income(s, e):
    return sum(float(b.get('amount', 0)) for b in db_select("bills", "amount", gte_filters={"bill_date": s}, lte_filters={"bill_date": e}))

def get_expense(s, e):
    return sum(float(x.get('amount', 0)) for x in db_select("expenses", "amount", gte_filters={"expense_date": s}, lte_filters={"expense_date": e}))

def get_period_dates(p):
    t = date.today()
    if p == "Daily": return t, t
    elif p == "Weekly": return t - timedelta(days=t.weekday()), t
    elif p == "Monthly": return t.replace(day=1), t
    elif p == "Yearly": return t.replace(month=1, day=1), t
    return t, t

def get_todays_birthdays():
    t = date.today()
    bdays = []
    for d in db_select("devotees", "name, dob"):
        if d.get('dob'):
            try:
                dob = datetime.strptime(str(d['dob']), '%Y-%m-%d').date()
                if dob.month == t.month and dob.day == t.day:
                    bdays.append(f"🎂 {d['name']} (Devotee)")
            except: pass
    for m in db_select("family_members", "name, dob"):
        if m.get('dob'):
            try:
                dob = datetime.strptime(str(m['dob']), '%Y-%m-%d').date()
                if dob.month == t.month and dob.day == t.day:
                    bdays.append(f"🎂 {m['name']} (Family)")
            except: pass
    return bdays

def gen_bill_no():
    return f"TMS-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:4].upper()}"

def make_whatsapp_link(phone, message):
    """Generate WhatsApp click-to-chat link"""
    phone_clean = ''.join(filter(str.isdigit, str(phone)))
    if len(phone_clean) == 10:
        phone_clean = "91" + phone_clean
    encoded_msg = urllib.parse.quote(message)
    return f"https://wa.me/{phone_clean}?text={encoded_msg}"

def parse_date_safe(val):
    """Safely parse date from various formats"""
    if val is None or str(val).strip() == '' or str(val).lower() == 'nan' or str(val).lower() == 'nat':
        return None
    val_str = str(val).strip()
    formats = ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d',
               '%d-%m-%y', '%d/%m/%y', '%m-%d-%Y', '%m-%d-%y']
    for fmt in formats:
        try:
            return datetime.strptime(val_str, fmt).date()
        except: pass
    try:
        ts = pd.Timestamp(val)
        if not pd.isna(ts):
            return ts.date()
    except: pass
    return None


# ============================================================
# DEFAULT AMMAN SVG
# ============================================================
DEFAULT_AMMAN_SVG = "data:image/svg+xml;base64," + base64.b64encode("""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="200" height="200">
  <defs>
    <radialGradient id="bg" cx="50%" cy="50%" r="50%">
      <stop offset="0%" style="stop-color:#fff5ee"/>
      <stop offset="100%" style="stop-color:#ffdab9"/>
    </radialGradient>
  </defs>
  <circle cx="100" cy="100" r="98" fill="url(#bg)" stroke="#ff6b35" stroke-width="3"/>
  <text x="100" y="75" text-anchor="middle" font-size="45">🙏</text>
  <text x="100" y="110" text-anchor="middle" font-size="13" fill="#8B0000" font-weight="bold">Sree</text>
  <text x="100" y="130" text-anchor="middle" font-size="11" fill="#8B0000" font-weight="bold">Bhadreshwari</text>
  <text x="100" y="148" text-anchor="middle" font-size="11" fill="#8B0000" font-weight="bold">Amman</text>
</svg>""".strip().encode()).decode()


# ============================================================
# BULK UPLOAD TEMPLATE GENERATOR
# ============================================================
def generate_excel_template():
    """Generate sample Excel template for bulk upload"""
    head_data = {
        'Sl.No': [1, 2],
        'Type': ['HEAD', 'HEAD'],
        'Family_Head_Name': ['Raman K', 'Suresh M'],
        'Address': ['12, Main St, City', '45, Temple Rd, Town'],
        'Mobile_No': ['9876543210', '9876543211'],
        'WhatsApp_No': ['9876543210', '9876543211'],
        'Relation_Type': ['Self', 'Self'],
        'Date_of_Birth': ['15-05-1980', '20-08-1975'],
        'Natchathiram': ['Ashwini', 'Rohini'],
        'Wedding_Day': ['10-06-2005', '15-01-2000'],
        'Yearly_Pooja': ['Archana;Abhishekam', 'Homam'],
        'Yearly_Pooja_Dates': ['15-01-2025;20-06-2025', '10-03-2025'],
    }

    member_data = {
        'Sl.No': [1.1, 1.2, 2.1],
        'Type': ['MEMBER', 'MEMBER', 'MEMBER'],
        'Family_Head_Name': ['Raman K', 'Raman K', 'Suresh M'],
        'Address': ['', '', ''],
        'Mobile_No': ['', '', ''],
        'WhatsApp_No': ['', '', ''],
        'Relation_Type': ['Spouse', 'Son', 'Spouse'],
        'Date_of_Birth': ['20-07-1985', '10-03-2008', '25-12-1980'],
        'Natchathiram': ['Bharani', 'Rohini', 'Magha'],
        'Wedding_Day': ['10-06-2005', '', '15-01-2000'],
        'Yearly_Pooja': ['', '', ''],
        'Yearly_Pooja_Dates': ['', '', ''],
    }

    # Combine
    all_data = {}
    for key in head_data:
        all_data[key] = head_data[key] + member_data[key]

    df = pd.DataFrame(all_data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Devotees')

        # Instructions sheet
        instr = pd.DataFrame({
            'Instructions': [
                'BULK UPLOAD TEMPLATE - Sree Bhadreshwari Amman Temple',
                '',
                '1. Type column: Use HEAD for family head, MEMBER for family members',
                '2. Family_Head_Name: For MEMBER rows, put the HEAD name to link them',
                '3. For MEMBER rows, Address/Mobile/WhatsApp are optional (inherited from HEAD)',
                '4. Date format: DD-MM-YYYY (e.g., 15-05-1980)',
                '5. Natchathiram: Use exact star names from the list',
                '6. Yearly_Pooja: Multiple poojas separated by semicolon (;)',
                '7. Yearly_Pooja_Dates: Corresponding dates separated by semicolon (;)',
                '8. Sl.No: Use 1, 2, 3 for heads. Use 1.1, 1.2 for members of head 1',
                '',
                'Valid Natchathiram values:',
                'Ashwini, Bharani, Karthigai, Rohini, Mrigashirsha, Thiruvadirai,',
                'Punarvasu, Pushya, Ashlesha, Magha, Purva Phalguni, Uttara Phalguni,',
                'Hasta, Chitra, Swati, Vishakha, Anuradha, Jyeshtha,',
                'Mula, Purva Ashadha, Uttara Ashadha, Shravana, Dhanishta, Shatabhisha,',
                'Purva Bhadrapada, Uttara Bhadrapada, Revati',
                '',
                'Valid Relation Types:',
                'Self, Spouse, Son, Daughter, Father, Mother, Brother, Sister,',
                'Grandfather, Grandmother, Father-in-law, Mother-in-law, etc.',
            ]
        })
        instr.to_excel(writer, index=False, sheet_name='Instructions')

    return output.getvalue()


def process_bulk_upload(df):
    """Process uploaded Excel data and insert into database"""
    results = {'success': 0, 'errors': [], 'members_added': 0, 'poojas_added': 0}
    head_id_map = {}  # Map head names to their database IDs

    required_cols = ['Type', 'Family_Head_Name']
    for col in required_cols:
        if col not in df.columns:
            results['errors'].append(f"Missing required column: {col}")
            return results

    # Process HEADs first
    heads = df[df['Type'].str.upper().str.strip() == 'HEAD']
    for idx, row in heads.iterrows():
        try:
            head_name = str(row.get('Family_Head_Name', '')).strip()
            if not head_name or head_name == 'nan':
                results['errors'].append(f"Row {idx+2}: Missing Family Head Name")
                continue

            dob = parse_date_safe(row.get('Date_of_Birth'))
            wedding = parse_date_safe(row.get('Wedding_Day'))

            devotee_data = {
                "name": head_name,
                "dob": str(dob) if dob else None,
                "relation_type": str(row.get('Relation_Type', 'Self')).strip() if str(row.get('Relation_Type', '')).strip() != 'nan' else 'Self',
                "mobile_no": str(row.get('Mobile_No', '')).strip() if str(row.get('Mobile_No', '')).strip() != 'nan' else '',
                "whatsapp_no": str(row.get('WhatsApp_No', '')).strip() if str(row.get('WhatsApp_No', '')).strip() != 'nan' else '',
                "wedding_day": str(wedding) if wedding else None,
                "natchathiram": str(row.get('Natchathiram', '')).strip() if str(row.get('Natchathiram', '')).strip() != 'nan' else None,
                "address": str(row.get('Address', '')).strip() if str(row.get('Address', '')).strip() != 'nan' else '',
            }

            result = db_insert("devotees", devotee_data)
            if result:
                head_id = result[0]['id']
                head_id_map[head_name.lower()] = head_id
                results['success'] += 1

                # Process yearly poojas
                poojas_str = str(row.get('Yearly_Pooja', '')).strip()
                dates_str = str(row.get('Yearly_Pooja_Dates', '')).strip()

                if poojas_str and poojas_str != 'nan':
                    poojas = [p.strip() for p in poojas_str.split(';') if p.strip()]
                    pooja_dates = [d.strip() for d in dates_str.split(';') if d.strip()] if dates_str != 'nan' else []

                    for i, pooja_name in enumerate(poojas):
                        p_date = parse_date_safe(pooja_dates[i]) if i < len(pooja_dates) else None
                        db_insert("devotee_yearly_pooja", {
                            "devotee_id": head_id,
                            "pooja_type": pooja_name,
                            "pooja_date": str(p_date) if p_date else None,
                            "description": "Bulk upload"
                        })
                        results['poojas_added'] += 1
            else:
                results['errors'].append(f"Row {idx+2}: Failed to insert {head_name}")

        except Exception as e:
            results['errors'].append(f"Row {idx+2}: {str(e)}")

    # Process MEMBERs
    members = df[df['Type'].str.upper().str.strip() == 'MEMBER']
    for idx, row in members.iterrows():
        try:
            member_name = str(row.get('Family_Head_Name', '')).strip()
            # Find the actual member name — for members, we use a different approach
            # The family head name links to parent; member's own name needs a field
            # Let's use Family_Head_Name as the link and Relation_Type has the role

            head_ref = str(row.get('Family_Head_Name', '')).strip().lower()
            if head_ref in head_id_map:
                head_id = head_id_map[head_ref]
            else:
                # Try to find in database
                devs = db_select("devotees", "id, name")
                found = False
                for d in devs:
                    if d['name'].lower().strip() == head_ref:
                        head_id = d['id']
                        head_id_map[head_ref] = head_id
                        found = True
                        break
                if not found:
                    results['errors'].append(f"Row {idx+2}: Head '{row.get('Family_Head_Name')}' not found")
                    continue

            # For members, we need their actual name
            # Use Address field as member name if it exists, otherwise use a combination
            member_actual_name = str(row.get('Address', '')).strip()
            if not member_actual_name or member_actual_name == 'nan':
                member_actual_name = f"Member of {row.get('Family_Head_Name', '')}"

            dob = parse_date_safe(row.get('Date_of_Birth'))
            wedding = parse_date_safe(row.get('Wedding_Day'))

            fm_data = {
                "devotee_id": head_id,
                "name": member_actual_name,
                "dob": str(dob) if dob else None,
                "relation_type": str(row.get('Relation_Type', '')).strip() if str(row.get('Relation_Type', '')).strip() != 'nan' else '',
                "wedding_day": str(wedding) if wedding else None,
                "natchathiram": str(row.get('Natchathiram', '')).strip() if str(row.get('Natchathiram', '')).strip() != 'nan' else None,
            }

            if db_insert("family_members", fm_data):
                results['members_added'] += 1
            else:
                results['errors'].append(f"Row {idx+2}: Failed to insert member")

        except Exception as e:
            results['errors'].append(f"Row {idx+2}: {str(e)}")

    return results


# ============================================================
# PAGE: LOGIN
# ============================================================
def page_login():
    bg = st.session_state.get('bg_image_base64')
    if bg:
        st.markdown(f"<style>.stApp{{background-image:url('{bg}');background-size:cover;}}</style>", unsafe_allow_html=True)
    else:
        st.markdown("<style>.stApp{background:linear-gradient(135deg,#fff5ee,#ffe4c4,#ffdab9,#fff5ee);}</style>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        amman = st.session_state.get('amman_photo_base64') or DEFAULT_AMMAN_SVG
        st.markdown(f'<div class="amman-photo-container"><img src="{amman}" class="amman-photo"></div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="temple-name-login">🛕 Sree Bhadreshwari Amman Temple<br>Management System</div>
        <div class="tamil-text">🙏 அம்மே நாராயணா ..தேவி நாராயணா 🙏</div>
        """, unsafe_allow_html=True)

        with st.form("login"):
            u = st.text_input("👤 Username")
            p = st.text_input("🔑 Password", type="password")
            if st.form_submit_button("🚀 Login", use_container_width=True):
                if not u or not p:
                    st.warning("⚠️ Enter both fields!")
                elif not DB_CONNECTED:
                    st.error("❌ DB not connected!")
                else:
                    users = db_select("users", filters={"username": u})
                    if users and users[0].get('password_hash') == p:
                        st.session_state.logged_in = True
                        st.session_state.username = u
                        st.session_state.user_role = users[0].get('role', 'user')
                        st.success("✅ Success!"); time.sleep(0.5); st.rerun()
                    else:
                        st.error("❌ Invalid credentials!")

        with st.expander("🎨 Customize Login"):
            au = st.file_uploader("Amman Photo", type=['jpg','jpeg','png'], key="au")
            if au:
                st.session_state.amman_photo_base64 = file_to_base64(au)
                st.rerun()
            bu = st.file_uploader("Background", type=['jpg','jpeg','png'], key="bu")
            if bu:
                st.session_state.bg_image_base64 = file_to_base64(bu)
                st.rerun()
            if st.button("🔄 Reset"):
                st.session_state.amman_photo_base64 = None
                st.session_state.bg_image_base64 = None
                st.rerun()

        st.markdown('<div style="text-align:center;color:#888;font-size:0.8em;margin-top:10px;">Default: admin / admin123</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# PAGE: DASHBOARD
# ============================================================
def page_dashboard():
    st.markdown("""
    <div class="main-header">
        <h1>🛕 Sree Bhadreshwari Amman Temple</h1>
        <p>🙏 அம்மே நாராயணா ..தேவி நாராயணா 🙏</p>
    </div>""", unsafe_allow_html=True)

    tparts = get_todays_birthdays()
    for n in db_select("news_ticker", filters={"is_active": True}):
        tparts.append(f"📢 {n['message']}")
    if not tparts:
        tparts.append("🛕 Welcome to Sree Bhadreshwari Amman Temple! 🙏")
    st.markdown(f'<div class="news-ticker-wrapper"><div class="news-ticker-text">{" &nbsp;⭐&nbsp; ".join(tparts)}</div></div>', unsafe_allow_html=True)

    period = st.selectbox("📅 Period", ["Daily", "Weekly", "Monthly", "Yearly"])
    s, e = get_period_dates(period)
    inc = get_income(s, e); exp = get_expense(s, e); bal = inc - exp
    td = len(db_select("devotees", "id"))

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f'<div class="metric-card income"><h3>💰 {period} Income</h3><h2>₹ {inc:,.2f}</h2></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card expense"><h3>💸 {period} Expenses</h3><h2>₹ {exp:,.2f}</h2></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card balance"><h3>💎 Balance</h3><h2>₹ {bal:,.2f}</h2></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="metric-card info"><h3>👥 Devotees</h3><h2>{td}</h2></div>', unsafe_allow_html=True)

    st.markdown("---")
    cl, cr = st.columns(2)
    with cl:
        st.markdown("### 🎂 Birthdays Today")
        bdays = get_todays_birthdays()
        if bdays:
            for b in bdays:
                st.markdown(f'<div class="birthday-card">🎉 {b} 🎈</div>', unsafe_allow_html=True)
        else: st.info("No birthdays today")

    with cr:
        st.markdown("### 🙏 Today's Pooja")
        for p in db_select("daily_pooja", filters={"pooja_date": str(date.today())}):
            ic = "✅" if p.get('status') == 'completed' else "⏳"
            st.markdown(f'<div class="pooja-card">{ic} <b>{p["pooja_name"]}</b> — {p.get("pooja_time","")}</div>', unsafe_allow_html=True)
            if p.get('status') != 'completed':
                if st.button("Complete", key=f"c_{p['id']}"):
                    db_update("daily_pooja", {"status": "completed"}, "id", p['id']); st.rerun()

        with st.expander("➕ Add Pooja"):
            with st.form("adp"):
                dn = st.text_input("Name", key="dpn")
                dt = st.text_input("Time", key="dpt")
                dd = st.date_input("Date", key="dpd")
                if st.form_submit_button("Add"):
                    if dn: db_insert("daily_pooja", {"pooja_name": dn, "pooja_time": dt, "pooja_date": str(dd), "status": "pending"}); st.rerun()

    st.markdown("---")
    st.bar_chart(pd.DataFrame({"Category": ["Income","Expenses","Balance"], "₹": [inc,exp,bal]}).set_index("Category"))


# ============================================================
# PAGE: DEVOTEE ENROLLMENT (with Bulk Upload)
# ============================================================
def page_devotee_enrollment():
    st.markdown('<div class="main-header"><h1>👥 Devotee Enrollment</h1><p>Register, Bulk Upload & Manage</p></div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["➕ New", "📤 Bulk Upload", "🔍 Search", "👨‍👩‍👧‍👦 Family"])

    with tab1:
        with st.form("enroll", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                nm = st.text_input("👤 Name *")
                db_ = st.date_input("📅 DOB", value=date(1990,1,1), min_value=MIN_DATE, max_value=MAX_DATE)
                rl = st.selectbox("👪 Relation", RELATION_TYPES)
                mb = st.text_input("📱 Mobile")
                wa = st.text_input("📲 WhatsApp")
            with c2:
                wd = st.date_input("💒 Wedding", value=None, min_value=MIN_DATE, max_value=MAX_DATE)
                nt = st.selectbox("⭐ Star", ["--"]+NATCHATHIRAM_LIST)
                ad = st.text_area("🏠 Address", height=80)
                ph = st.file_uploader("📷 Photo", type=['jpg','jpeg','png'])

            st.markdown("#### 🙏 Yearly Pooja")
            yc1, yc2, yc3 = st.columns(3)
            ptl = [p['name'] for p in db_select("pooja_types", "name")]
            with yc1: ypt = st.selectbox("Type", ["--"]+ptl, key="y1t")
            with yc2: ypd = st.date_input("Date", key="y1d", min_value=MIN_DATE, max_value=MAX_DATE)
            with yc3: ypdesc = st.text_input("Desc", key="y1dc")

            if st.form_submit_button("✅ Register", use_container_width=True):
                if nm.strip():
                    r = db_insert("devotees", {
                        "name": nm.strip(), "dob": str(db_), "relation_type": rl,
                        "mobile_no": mb, "whatsapp_no": wa,
                        "wedding_day": str(wd) if wd else None,
                        "natchathiram": nt if nt != "--" else None,
                        "address": ad, "photo_url": file_to_base64(ph)
                    })
                    if r:
                        if ypt != "--":
                            db_insert("devotee_yearly_pooja", {"devotee_id": r[0]['id'], "pooja_type": ypt, "pooja_date": str(ypd), "description": ypdesc})
                        st.success(f"✅ '{nm}' enrolled!"); st.rerun()
                else: st.error("❌ Name required!")

    # ---- BULK UPLOAD TAB ----
    with tab2:
        st.markdown("### 📤 Bulk Upload Devotees from Excel")
        st.markdown("""
        Upload an Excel file to register multiple devotees and family members at once.
        Download the template first, fill it in, then upload.
        """)

        st.markdown("#### 📥 Step 1: Download Template")
        template_data = generate_excel_template()
        st.download_button(
            "📥 Download Excel Template",
            data=template_data,
            file_name="devotee_bulk_upload_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

        st.markdown("---")
        st.markdown("#### 📤 Step 2: Upload Filled Excel")
        st.markdown("""
        **Excel Format:**
        | Sl.No | Type | Family_Head_Name | Address | Mobile_No | WhatsApp_No | Relation_Type | Date_of_Birth | Natchathiram | Wedding_Day | Yearly_Pooja | Yearly_Pooja_Dates |
        |-------|------|-----------------|---------|-----------|-------------|---------------|---------------|-------------|-------------|-------------|-------------------|
        | 1 | HEAD | Raman K | 12 Main St | 9876543210 | 9876543210 | Self | 15-05-1980 | Ashwini | 10-06-2005 | Archana;Abhishekam | 15-01-2025;20-06-2025 |
        | 1.1 | MEMBER | Raman K | Lakshmi R | | | Spouse | 20-07-1985 | Bharani | 10-06-2005 | | |

        **Note for MEMBER rows:** Put the member's actual name in the **Address** column. The Family_Head_Name links the member to their family head.
        """)

        uploaded_file = st.file_uploader("📁 Upload Excel File", type=['xlsx', 'xls'], key="bulk_upload")

        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file, sheet_name=0)
                st.markdown("#### 👀 Preview")
                st.dataframe(df.head(20), use_container_width=True, hide_index=True)

                st.markdown(f"**Total Rows:** {len(df)} | **Heads:** {len(df[df['Type'].str.upper().str.strip()=='HEAD'])} | **Members:** {len(df[df['Type'].str.upper().str.strip()=='MEMBER'])}")

                if st.button("🚀 Process & Upload", use_container_width=True, type="primary"):
                    with st.spinner("Processing... Please wait..."):
                        results = process_bulk_upload(df)

                    st.markdown("---")
                    st.markdown("### 📊 Upload Results")

                    rc1, rc2, rc3 = st.columns(3)
                    with rc1:
                        st.markdown(f'<div class="metric-card income"><h3>✅ Heads Added</h3><h2>{results["success"]}</h2></div>', unsafe_allow_html=True)
                    with rc2:
                        st.markdown(f'<div class="metric-card balance"><h3>👨‍👩‍👧 Members Added</h3><h2>{results["members_added"]}</h2></div>', unsafe_allow_html=True)
                    with rc3:
                        st.markdown(f'<div class="metric-card info"><h3>🙏 Poojas Added</h3><h2>{results["poojas_added"]}</h2></div>', unsafe_allow_html=True)

                    if results['errors']:
                        st.markdown("### ⚠️ Errors")
                        for err in results['errors']:
                            st.markdown(f'<div class="upload-error">❌ {err}</div>', unsafe_allow_html=True)

                    if results['success'] > 0:
                        st.balloons()

            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")

    # ---- SEARCH TAB ----
    with tab3:
        sc1, sc2, sc3 = st.columns(3)
        with sc1: sn = st.text_input("Name", key="sn")
        with sc2: sm = st.text_input("Mobile", key="sm")
        with sc3: sa = st.text_input("Address", key="sa")

        devs = db_select("devotees")
        if sn: devs = [d for d in devs if sn.lower() in d.get('name','').lower()]
        if sm: devs = [d for d in devs if sm in d.get('mobile_no','')]
        if sa: devs = [d for d in devs if sa.lower() in d.get('address','').lower()]

        st.markdown(f"**Found: {len(devs)}**")
        for dev in devs:
            with st.expander(f"👤 {dev['name']} | 📱 {dev.get('mobile_no','N/A')}"):
                dc1, dc2 = st.columns([3,1])
                with dc1:
                    for l,k in [("Name","name"),("DOB","dob"),("Mobile","mobile_no"),("WhatsApp","whatsapp_no"),
                                ("Relation","relation_type"),("Wedding","wedding_day"),("Star","natchathiram"),("Address","address")]:
                        st.write(f"**{l}:** {dev.get(k,'N/A')}")
                with dc2:
                    if dev.get('photo_url') and dev['photo_url'].startswith('data:'):
                        st.markdown(f'<img src="{dev["photo_url"]}" width="120" style="border-radius:10px">', unsafe_allow_html=True)

                st.markdown("**🙏 Yearly Poojas:**")
                for yp in db_select("devotee_yearly_pooja", filters={"devotee_id": dev['id']}):
                    ypc1, ypc2 = st.columns([5,1])
                    with ypc1: st.write(f"• {yp['pooja_type']} — {yp.get('pooja_date','')}")
                    with ypc2:
                        if st.button("❌", key=f"dyp_{yp['id']}"): db_delete("devotee_yearly_pooja","id",yp['id']); st.rerun()

                with st.form(f"ayp_{dev['id']}"):
                    ayc1,ayc2,ayc3=st.columns(3)
                    ptn=[p['name'] for p in db_select("pooja_types","name")]
                    with ayc1: nypt=st.selectbox("Type",["--"]+ptn,key=f"nt_{dev['id']}")
                    with ayc2: nypd=st.date_input("Date",key=f"nd_{dev['id']}",min_value=MIN_DATE,max_value=MAX_DATE)
                    with ayc3: nypdsc=st.text_input("Desc",key=f"ndc_{dev['id']}")
                    if st.form_submit_button("Add"):
                        if nypt!="--": db_insert("devotee_yearly_pooja",{"devotee_id":dev['id'],"pooja_type":nypt,"pooja_date":str(nypd),"description":nypdsc}); st.rerun()

                bc1,bc2=st.columns(2)
                with bc1:
                    if st.button("✏️ Edit",key=f"e_{dev['id']}"):
                        st.session_state[f"ed_{dev['id']}"]=not st.session_state.get(f"ed_{dev['id']}",False); st.rerun()
                with bc2:
                    if st.button("🗑️ Delete",key=f"d_{dev['id']}"):
                        db_delete("devotee_yearly_pooja","devotee_id",dev['id'])
                        db_delete("family_members","devotee_id",dev['id'])
                        db_delete("devotees","id",dev['id']); st.rerun()

                if st.session_state.get(f"ed_{dev['id']}",False):
                    with st.form(f"ef_{dev['id']}"):
                        ec1,ec2=st.columns(2)
                        with ec1:
                            en=st.text_input("Name",value=dev.get('name',''),key=f"en_{dev['id']}")
                            edv=date(1990,1,1)
                            try: edv=datetime.strptime(str(dev.get('dob','')),"%Y-%m-%d").date()
                            except: pass
                            ed=st.date_input("DOB",value=edv,key=f"ed2_{dev['id']}",min_value=MIN_DATE,max_value=MAX_DATE)
                            em=st.text_input("Mobile",value=dev.get('mobile_no',''),key=f"em_{dev['id']}")
                            ew=st.text_input("WhatsApp",value=dev.get('whatsapp_no',''),key=f"ew_{dev['id']}")
                        with ec2:
                            er=st.selectbox("Relation",RELATION_TYPES,index=RELATION_TYPES.index(dev['relation_type']) if dev.get('relation_type') in RELATION_TYPES else 0,key=f"er_{dev['id']}")
                            so=["--"]+NATCHATHIRAM_LIST
                            cs=dev.get('natchathiram','--')
                            es=st.selectbox("Star",so,index=so.index(cs) if cs in so else 0,key=f"es_{dev['id']}")
                            ea=st.text_area("Address",value=dev.get('address',''),key=f"ea_{dev['id']}")
                        if st.form_submit_button("💾 Save"):
                            db_update("devotees",{"name":en,"dob":str(ed),"mobile_no":em,"whatsapp_no":ew,"relation_type":er,"natchathiram":es if es!="--" else None,"address":ea},"id",dev['id'])
                            st.session_state[f"ed_{dev['id']}"]=False; st.rerun()

    # ---- FAMILY TAB ----
    with tab4:
        ds=db_select("devotees","id,name,mobile_no")
        if not ds: st.info("No devotees"); return
        do={f"{d['name']} ({d.get('mobile_no','')})":d['id'] for d in ds}
        sh=st.selectbox("Family Head",list(do.keys()))
        hi=do[sh]
        for fm in db_select("family_members",filters={"devotee_id":hi}):
            fc1,fc2=st.columns([5,1])
            with fc1: st.write(f"👤 **{fm['name']}** | {fm.get('relation_type','')} | DOB: {fm.get('dob','')}")
            with fc2:
                if st.button("🗑️",key=f"dfm_{fm['id']}"): db_delete("family_members","id",fm['id']); st.rerun()

        with st.form("afm",clear_on_submit=True):
            fc1,fc2=st.columns(2)
            with fc1:
                fn=st.text_input("Name *")
                fd=st.date_input("DOB",value=date(1995,1,1),min_value=MIN_DATE,max_value=MAX_DATE)
                fr=st.selectbox("Relation",RELATION_TYPES)
            with fc2:
                fw=st.date_input("Wedding",value=None,min_value=MIN_DATE,max_value=MAX_DATE,key="fmw")
                fs=st.selectbox("Star",["--"]+NATCHATHIRAM_LIST,key="fms")
            if st.form_submit_button("➕ Add",use_container_width=True):
                if fn.strip():
                    db_insert("family_members",{"devotee_id":hi,"name":fn.strip(),"dob":str(fd),"relation_type":fr,"wedding_day":str(fw) if fw else None,"natchathiram":fs if fs!="--" else None})
                    st.success(f"✅ Added!"); st.rerun()


# ============================================================
# PAGE: BILLING (with PDF & WhatsApp)
# ============================================================
def page_billing():
    st.markdown('<div class="main-header"><h1>🧾 Billing</h1><p>Generate bills with PDF download & WhatsApp sharing</p></div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["➕ New Bill", "📋 History"])

    with tab1:
        dt = st.radio("Type", ["Enrolled Devotee", "Guest Devotee"], horizontal=True)
        bc1, bc2 = st.columns(2)

        with bc1:
            mb = st.text_input("📝 Manual Bill No")
            bb = st.text_input("📖 Bill Book No")
            ptd = db_select("pooja_types")
            pto = {f"{p['name']} — ₹{p.get('amount',0)}": p for p in ptd} if ptd else {}
            sp = st.selectbox("🙏 Pooja", list(pto.keys()) if pto else ["None"])
            da = float(pto[sp].get('amount',0)) if sp in pto else 0.0
            am = st.number_input("💰 Amount", value=da, min_value=0.0, step=10.0)
            bd = st.date_input("📅 Date", value=date.today())

        with bc2:
            did = None; gn=ga=gm=gw=""
            if dt == "Enrolled Devotee":
                st.markdown("### 🔍 Search")
                sby = st.selectbox("By", ["Name","Mobile","WhatsApp","Address"])
                sv = st.text_input(f"Enter {sby}")
                ad = db_select("devotees")
                if sv:
                    fm = {"Name":"name","Mobile":"mobile_no","WhatsApp":"whatsapp_no","Address":"address"}
                    ad = [d for d in ad if sv.lower() in str(d.get(fm[sby],'')).lower()]
                if ad:
                    dm = {f"{d['name']} — {d.get('mobile_no','N/A')}": d for d in ad}
                    ch = st.selectbox("Select", list(dm.keys()))
                    if ch:
                        sd = dm[ch]; did = sd['id']
                        st.markdown(f'<div class="success-box">👤 <b>{sd["name"]}</b><br>📱 {sd.get("mobile_no","N/A")} 📲 {sd.get("whatsapp_no","N/A")}<br>🏠 {sd.get("address","N/A")}</div>', unsafe_allow_html=True)
                else: st.warning("No match")
            else:
                st.markdown("### 👤 Guest")
                gn=st.text_input("Name *")
                ga=st.text_area("Address *",height=70)
                gm=st.text_input("📱 Mobile")
                gw=st.text_input("📲 WhatsApp")

        if st.button("🧾 Generate Bill", use_container_width=True, type="primary"):
            ok=True
            if dt=="Enrolled Devotee" and not did: st.error("❌ Select devotee!"); ok=False
            if dt=="Guest Devotee" and not gn.strip(): st.error("❌ Name!"); ok=False
            if am<=0: st.error("❌ Amount!"); ok=False

            if ok:
                bn=gen_bill_no()
                pn=sp.split(" — ")[0] if " — " in sp else sp
                bdata={"bill_no":bn,"manual_bill_no":mb,"bill_book_no":bb,
                       "devotee_type":"enrolled" if dt=="Enrolled Devotee" else "guest",
                       "devotee_id":did,"guest_name":gn if dt=="Guest Devotee" else None,
                       "guest_address":ga if dt=="Guest Devotee" else None,
                       "guest_mobile":gm if dt=="Guest Devotee" else None,
                       "guest_whatsapp":gw if dt=="Guest Devotee" else None,
                       "pooja_type":pn,"amount":am,"bill_date":str(bd)}
                res=db_insert("bills",bdata)

                if res:
                    # Get details for PDF
                    if dt=="Enrolled Devotee" and did:
                        di=db_select("devotees",filters={"id":did})
                        bname=di[0]['name'] if di else "N/A"
                        baddr=di[0].get('address','') if di else ""
                        bmob=di[0].get('mobile_no','') if di else ""
                        bwa=di[0].get('whatsapp_no','') if di else ""
                    else:
                        bname,baddr,bmob,bwa=gn,ga,gm,gw

                    st.success(f"✅ Bill: {bn}")

                    # Generate PDF
                    if PDF_AVAILABLE:
                        pdf_bytes = generate_bill_pdf(bn, mb, bb, bd, bname, baddr, bmob, pn, am)
                        st.session_state.last_bill_pdf = pdf_bytes
                        st.session_state.last_bill_info = {
                            'bill_no': bn, 'name': bname, 'amount': am,
                            'pooja': pn, 'date': str(bd), 'wa_no': bwa or bmob
                        }

                    # Bill Preview
                    st.markdown(f"""
                    <div style="background:#fffdf7;padding:25px;border:2px solid #ff6b35;border-radius:15px;max-width:550px;margin:20px auto;">
                        <div style="text-align:center;border-bottom:2px solid #ff6b35;padding-bottom:12px;">
                            <h2 style="color:#8B0000;margin:0;">🛕 Sree Bhadreshwari Amman Temple</h2>
                            <p style="margin:3px 0;">🙏 அம்மே நாராயணா 🙏</p>
                        </div>
                        <table style="width:100%;margin:15px 0;">
                            <tr><td><b>Bill No:</b></td><td>{bn}</td></tr>
                            <tr><td><b>Manual Bill:</b></td><td>{mb}</td></tr>
                            <tr><td><b>Book No:</b></td><td>{bb}</td></tr>
                            <tr><td><b>Date:</b></td><td>{bd}</td></tr>
                            <tr><td colspan="2"><hr style="border:1px dashed #ccc"></td></tr>
                            <tr><td><b>Name:</b></td><td>{bname}</td></tr>
                            <tr><td><b>Address:</b></td><td>{baddr}</td></tr>
                            <tr><td><b>Mobile:</b></td><td>{bmob}</td></tr>
                            <tr><td colspan="2"><hr style="border:1px dashed #ccc"></td></tr>
                            <tr><td><b>Pooja:</b></td><td>{pn}</td></tr>
                            <tr><td><b>Amount:</b></td><td style="font-size:1.4em;color:#11998e"><b>₹ {am:,.2f}</b></td></tr>
                        </table>
                        <div style="text-align:center;border-top:2px solid #ff6b35;padding-top:10px;">
                            <p style="color:#666;margin:0;">🙏 அம்மே நாராயணா ..தேவி நாராயணா 🙏</p>
                        </div>
                    </div>""", unsafe_allow_html=True)

                    # PDF Download & WhatsApp buttons
                    st.markdown("---")
                    st.markdown("### 📥 Download & Share")

                    dl_col1, dl_col2 = st.columns(2)

                    with dl_col1:
                        if PDF_AVAILABLE and st.session_state.last_bill_pdf:
                            st.download_button(
                                "📥 Download Bill PDF",
                                data=st.session_state.last_bill_pdf,
                                file_name=f"Bill_{bn}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                        else:
                            st.warning("PDF generation not available")

                    with dl_col2:
                        wa_number = bwa or bmob
                        if wa_number:
                            wa_message = (
                                f"🛕 *Sree Bhadreshwari Amman Temple*\n"
                                f"🙏 அம்மே நாராயணா\n\n"
                                f"📄 *BILL / RECEIPT*\n"
                                f"━━━━━━━━━━━━━━━━\n"
                                f"Bill No: {bn}\n"
                                f"Date: {bd}\n"
                                f"Name: {bname}\n"
                                f"Pooja: {pn}\n"
                                f"*Amount: ₹ {am:,.2f}*\n"
                                f"━━━━━━━━━━━━━━━━\n"
                                f"🙏 Thank you for your contribution!\n"
                                f"அம்மே நாராயணா ..தேவி நாராயணா"
                            )
                            wa_link = make_whatsapp_link(wa_number, wa_message)
                            st.markdown(f'<a href="{wa_link}" target="_blank" class="wa-btn">📲 Send via WhatsApp</a>', unsafe_allow_html=True)
                            st.caption(f"Will send to: {wa_number}")
                        else:
                            st.info("No WhatsApp number available")

    with tab2:
        st.markdown("### 📋 Bills")
        bills=sorted(db_select("bills"),key=lambda x:x.get('created_at',''),reverse=True)
        for b in bills:
            bname=b.get('guest_name','')
            if b.get('devotee_type')=='enrolled' and b.get('devotee_id'):
                dd=db_select("devotees","name,mobile_no,whatsapp_no",filters={"id":b['devotee_id']})
                if dd: bname=dd[0]['name']

            with st.expander(f"🧾 {b.get('bill_no','')} | {bname} | {b.get('pooja_type','')} | ₹{b.get('amount',0)}"):
                st.write(f"**Bill:** {b.get('bill_no','')} | **Manual:** {b.get('manual_bill_no','')} | **Book:** {b.get('bill_book_no','')}")
                st.write(f"**Pooja:** {b.get('pooja_type','')} | **Amount:** ₹{float(b.get('amount',0)):,.2f} | **Date:** {b.get('bill_date','')}")

                if b.get('guest_name'): st.write(f"**Guest:** {b['guest_name']} | 📱{b.get('guest_mobile','')}")

                # Re-download PDF and re-send WhatsApp for existing bills
                hc1, hc2, hc3 = st.columns(3)

                with hc1:
                    if PDF_AVAILABLE:
                        # Get bill details for PDF regeneration
                        if b.get('devotee_type')=='enrolled' and b.get('devotee_id'):
                            di=db_select("devotees",filters={"id":b['devotee_id']})
                            pname=di[0]['name'] if di else "N/A"
                            paddr=di[0].get('address','') if di else ""
                            pmob=di[0].get('mobile_no','') if di else ""
                        else:
                            pname=b.get('guest_name','')
                            paddr=b.get('guest_address','')
                            pmob=b.get('guest_mobile','')

                        rpdf = generate_bill_pdf(
                            b.get('bill_no',''), b.get('manual_bill_no',''),
                            b.get('bill_book_no',''), b.get('bill_date',''),
                            pname, paddr, pmob, b.get('pooja_type',''), b.get('amount',0)
                        )
                        st.download_button("📥 PDF", data=rpdf,
                                          file_name=f"Bill_{b.get('bill_no','')}.pdf",
                                          mime="application/pdf",
                                          key=f"pdf_{b['id']}")

                with hc2:
                    # WhatsApp resend
                    wa_num = ""
                    if b.get('devotee_type')=='enrolled' and b.get('devotee_id'):
                        di=db_select("devotees","whatsapp_no,mobile_no",filters={"id":b['devotee_id']})
                        if di: wa_num = di[0].get('whatsapp_no','') or di[0].get('mobile_no','')
                    else:
                        wa_num = b.get('guest_whatsapp','') or b.get('guest_mobile','')

                    if wa_num:
                        msg = f"🛕 Sree Bhadreshwari Amman Temple\nBill: {b.get('bill_no','')}\nPooja: {b.get('pooja_type','')}\nAmount: ₹{float(b.get('amount',0)):,.2f}\nDate: {b.get('bill_date','')}"
                        wl = make_whatsapp_link(wa_num, msg)
                        st.markdown(f'<a href="{wl}" target="_blank" class="wa-btn" style="font-size:0.8em;padding:6px 12px;">📲 WhatsApp</a>', unsafe_allow_html=True)

                with hc3:
                    if st.session_state.user_role=='admin':
                        if st.button("🗑️",key=f"db_{b['id']}"):
                            db_delete("bills","id",b['id']); st.rerun()


# ============================================================
# PAGE: EXPENSES
# ============================================================
def page_expenses():
    st.markdown('<div class="main-header"><h1>💸 Expenses</h1><p>Track expenses</p></div>', unsafe_allow_html=True)
    t1,t2=st.tabs(["➕ Add","📋 History"])
    with t1:
        with st.form("ef",clear_on_submit=True):
            c1,c2=st.columns(2)
            with c1:
                etn=[e['name'] for e in db_select("expense_types","name")] or ["Misc"]
                et=st.selectbox("Type",etn); ea=st.number_input("Amount",min_value=0.0,step=10.0)
            with c2:
                ed=st.date_input("Date"); edesc=st.text_area("Description",height=80)
            if st.form_submit_button("💾 Save",use_container_width=True):
                if ea>0: db_insert("expenses",{"expense_type":et,"amount":ea,"description":edesc,"expense_date":str(ed)}); st.rerun()
    with t2:
        exps=sorted(db_select("expenses"),key=lambda x:x.get('expense_date',''),reverse=True)
        if exps:
            st.metric("Total",f"₹ {sum(float(e.get('amount',0)) for e in exps):,.2f}")
            st.dataframe(pd.DataFrame([{"Date":e.get('expense_date',''),"Type":e.get('expense_type',''),"Amount":f"₹{float(e.get('amount',0)):,.2f}","Desc":e.get('description','')} for e in exps]),use_container_width=True,hide_index=True)


# ============================================================
# PAGE: REPORTS
# ============================================================
def page_reports():
    st.markdown('<div class="main-header"><h1>📊 Reports</h1><p>Financial reports</p></div>', unsafe_allow_html=True)
    rc1,rc2,rc3=st.columns(3)
    with rc1: period=st.selectbox("Period",["Daily","Weekly","Monthly","Yearly","Custom"])
    t=date.today()
    if period=="Custom":
        with rc2: sd=st.date_input("From",value=t-timedelta(30))
        with rc3: ed=st.date_input("To",value=t)
    else: sd,ed=get_period_dates(period)
    ptn=["All"]+[p['name'] for p in db_select("pooja_types","name")]
    pf=st.selectbox("Pooja Filter",ptn)
    bills=db_select("bills",gte_filters={"bill_date":sd},lte_filters={"bill_date":ed})
    exps=db_select("expenses",gte_filters={"expense_date":sd},lte_filters={"expense_date":ed})
    if pf!="All": bills=[b for b in bills if b.get('pooja_type')==pf]
    ti=sum(float(b.get('amount',0)) for b in bills)
    te=sum(float(e.get('amount',0)) for e in exps)
    mc1,mc2,mc3=st.columns(3)
    with mc1: st.markdown(f'<div class="metric-card income"><h3>Income</h3><h2>₹{ti:,.2f}</h2></div>',unsafe_allow_html=True)
    with mc2: st.markdown(f'<div class="metric-card expense"><h3>Expenses</h3><h2>₹{te:,.2f}</h2></div>',unsafe_allow_html=True)
    with mc3: st.markdown(f'<div class="metric-card balance"><h3>Balance</h3><h2>₹{ti-te:,.2f}</h2></div>',unsafe_allow_html=True)
    rt1,rt2,rt3=st.tabs(["Income","Expenses","Charts"])
    with rt1:
        if bills:
            df=pd.DataFrame([{"Bill":b.get('bill_no',''),"Date":b.get('bill_date',''),"Pooja":b.get('pooja_type',''),"Amount":float(b.get('amount',0))} for b in bills])
            st.dataframe(df,use_container_width=True,hide_index=True)
            st.download_button("📥 CSV",df.to_csv(index=False),"income.csv")
    with rt2:
        if exps:
            df=pd.DataFrame([{"Date":e.get('expense_date',''),"Type":e.get('expense_type',''),"Amount":float(e.get('amount',0))} for e in exps])
            st.dataframe(df,use_container_width=True,hide_index=True)
    with rt3:
        if bills or exps:
            st.bar_chart(pd.DataFrame({"Cat":["Income","Expenses"],"₹":[ti,te]}).set_index("Cat"))


# ============================================================
# PAGE: ASSET MANAGEMENT
# ============================================================
def page_assets():
    st.markdown('<div class="main-header"><h1>🏷️ Asset Management</h1><p>Track temple assets</p></div>', unsafe_allow_html=True)
    t1,t2=st.tabs(["➕ Add","📋 List"])
    with t1:
        with st.form("af",clear_on_submit=True):
            c1,c2=st.columns(2)
            with c1:
                at=st.text_input("🏷️ Tag *"); an=st.text_input("📦 Name *"); sn=st.text_input("🔢 Serial No")
            with c2:
                dn=st.text_input("🙏 Donor"); dd=st.date_input("📅 Date",min_value=MIN_DATE,max_value=MAX_DATE)
                ai=st.file_uploader("📷 Image",type=['jpg','jpeg','png'])
            ad=st.text_area("Notes",height=60)
            if st.form_submit_button("✅ Register",use_container_width=True):
                if at.strip() and an.strip():
                    db_insert("assets",{"asset_tag":at.strip(),"asset_name":an.strip(),"serial_no":sn,"donor_name":dn,"donation_date":str(dd),"image_url":file_to_base64(ai),"description":ad})
                    st.success("✅ Added!"); st.rerun()
    with t2:
        sa=st.text_input("🔍 Search",key="sa2")
        assets=db_select("assets")
        if sa: assets=[a for a in assets if sa.lower() in a.get('asset_tag','').lower() or sa.lower() in a.get('asset_name','').lower() or sa.lower() in a.get('donor_name','').lower()]
        for a in assets:
            with st.expander(f"🏷️ {a.get('asset_tag','')} | {a.get('asset_name','')}"):
                ac1,ac2=st.columns([3,1])
                with ac1:
                    for l,k in [("Tag","asset_tag"),("Name","asset_name"),("Serial","serial_no"),("Donor","donor_name"),("Date","donation_date"),("Notes","description")]:
                        st.write(f"**{l}:** {a.get(k,'N/A')}")
                with ac2:
                    if a.get('image_url') and a['image_url'].startswith('data:'):
                        st.markdown(f'<img src="{a["image_url"]}" width="130" style="border-radius:10px">', unsafe_allow_html=True)
                if st.button("🗑️ Delete",key=f"da_{a['id']}"): db_delete("assets","id",a['id']); st.rerun()


# ============================================================
# PAGE: SETTINGS
# ============================================================
def page_settings():
    st.markdown('<div class="main-header"><h1>⚙️ Settings</h1><p>Configuration</p></div>', unsafe_allow_html=True)
    t1,t2,t3=st.tabs(["🙏 Pooja","💸 Expense","📢 News"])
    with t1:
        for p in db_select("pooja_types"):
            c1,c2=st.columns([5,1])
            with c1: st.write(f"🙏 **{p['name']}** — ₹{p.get('amount',0)}")
            with c2:
                if st.button("🗑️",key=f"dp_{p['id']}"): db_delete("pooja_types","id",p['id']); st.rerun()
        with st.form("apt",clear_on_submit=True):
            c1,c2=st.columns(2)
            with c1: nn=st.text_input("Name")
            with c2: na=st.number_input("Amount",min_value=0.0,step=10.0)
            if st.form_submit_button("➕"): 
                if nn.strip(): db_insert("pooja_types",{"name":nn.strip(),"amount":na}); st.rerun()
    with t2:
        for e in db_select("expense_types"):
            c1,c2=st.columns([5,1])
            with c1: st.write(f"💸 **{e['name']}**")
            with c2:
                if st.button("🗑️",key=f"de_{e['id']}"): db_delete("expense_types","id",e['id']); st.rerun()
        with st.form("aet",clear_on_submit=True):
            nn=st.text_input("Name")
            if st.form_submit_button("➕"):
                if nn.strip(): db_insert("expense_types",{"name":nn.strip()}); st.rerun()
    with t3:
        for n in db_select("news_ticker"):
            c1,c2,c3=st.columns([4,1,1])
            with c1: st.write(f"{'🟢' if n.get('is_active') else '🔴'} {n['message']}")
            with c2:
                if st.button("Toggle",key=f"tn_{n['id']}"): db_update("news_ticker",{"is_active":not n.get('is_active',True)},"id",n['id']); st.rerun()
            with c3:
                if st.button("🗑️",key=f"dn_{n['id']}"): db_delete("news_ticker","id",n['id']); st.rerun()
        with st.form("an",clear_on_submit=True):
            nm=st.text_input("Message")
            if st.form_submit_button("➕"):
                if nm.strip(): db_insert("news_ticker",{"message":nm.strip(),"is_active":True}); st.rerun()


# ============================================================
# PAGE: USERS
# ============================================================
def page_users():
    st.markdown('<div class="main-header"><h1>👥 Users</h1><p>Manage</p></div>', unsafe_allow_html=True)
    if st.session_state.user_role!='admin': st.error("Admin only!"); return
    t1,t2=st.tabs(["➕ Create","📋 List"])
    with t1:
        with st.form("cu",clear_on_submit=True):
            c1,c2=st.columns(2)
            with c1: nu=st.text_input("User"); np=st.text_input("Pass",type="password")
            with c2: cp=st.text_input("Confirm",type="password"); nr=st.selectbox("Role",["user","admin"])
            if st.form_submit_button("➕",use_container_width=True):
                if nu and np and np==cp and not db_select("users",filters={"username":nu}):
                    db_insert("users",{"username":nu,"password_hash":np,"role":nr}); st.success("✅"); st.rerun()
    with t2:
        for u in db_select("users"):
            c1,c2=st.columns([5,1])
            with c1: st.write(f"{'👑' if u.get('role')=='admin' else '👤'} **{u['username']}**")
            with c2:
                if u['username']!='admin':
                    if st.button("🗑️",key=f"du_{u['id']}"): db_delete("users","id",u['id']); st.rerun()


# ============================================================
# PAGE: SAMAYA VAKUPPU
# ============================================================
def page_samaya():
    st.markdown('<div class="main-header"><h1>📚 Samaya Vakuppu</h1><p>Students</p></div>', unsafe_allow_html=True)
    t1,t2=st.tabs(["➕ Add","📋 List"])
    with t1:
        with st.form("sv",clear_on_submit=True):
            c1,c2=st.columns(2)
            with c1:
                sn=st.text_input("Name *"); sd=st.date_input("DOB",value=date(2010,1,1),min_value=MIN_DATE,max_value=MAX_DATE)
                sa=st.text_area("Address",height=60); spt=st.selectbox("Parent",["Father","Mother"]); spn=st.text_input("Parent Name")
            with c2:
                sbd=st.date_input("Bond Date",min_value=MIN_DATE,max_value=MAX_DATE); sbk=st.text_input("Bank"); sbr=st.text_input("Branch")
                sbn=st.text_input("Bond No"); sbf=st.file_uploader("Bond Scan",type=['jpg','jpeg','png','pdf'],key="svb"); sph=st.file_uploader("Photo",type=['jpg','jpeg','png'],key="svp")
            if st.form_submit_button("✅",use_container_width=True):
                if sn.strip(): db_insert("samaya_vakuppu",{"student_name":sn.strip(),"dob":str(sd),"address":sa,"parent_name":spn,"parent_type":spt,"bond_issue_date":str(sbd),"scanned_bond_url":file_to_base64(sbf),"photo_url":file_to_base64(sph),"bond_issuing_bank":sbk,"branch_of_bank":sbr,"bond_no":sbn}); st.rerun()
    with t2:
        for s in db_select("samaya_vakuppu"):
            with st.expander(f"👤 {s['student_name']}"):
                for l,k in [("Name","student_name"),("DOB","dob"),("Address","address"),("Parent","parent_name"),("Bond","bond_no")]:
                    st.write(f"**{l}:** {s.get(k,'N/A')}")
                if st.button("🗑️",key=f"ds_{s['id']}"): db_delete("samaya_vakuppu","id",s['id']); st.rerun()


# ============================================================
# PAGE: THIRUMANA MANDAPAM
# ============================================================
def page_thirumana():
    st.markdown('<div class="main-header"><h1>💒 Thirumana Mandapam</h1><p>Bonds</p></div>', unsafe_allow_html=True)
    t1,t2=st.tabs(["➕ Add","📋 List"])
    with t1:
        with st.form("tm",clear_on_submit=True):
            c1,c2=st.columns(2)
            with c1: tn=st.text_input("Name *"); ta=st.text_area("Address",height=60); tb=st.text_input("Bond No"); td=st.date_input("Date",min_value=MIN_DATE,max_value=MAX_DATE)
            with c2: tam=st.number_input("Amount",min_value=0.0,step=100.0); tnb=st.number_input("No. Bonds",min_value=0,step=1); ts=st.file_uploader("Scan",type=['jpg','jpeg','png','pdf'],key="tms"); tp=st.file_uploader("Photo",type=['jpg','jpeg','png'],key="tmp")
            if st.form_submit_button("✅",use_container_width=True):
                if tn.strip(): db_insert("thirumana_mandapam",{"name":tn.strip(),"address":ta,"bond_no":tb,"bond_issued_date":str(td),"amount":tam,"no_of_bonds":tnb,"scan_copy_url":file_to_base64(ts),"photo_url":file_to_base64(tp)}); st.rerun()
    with t2:
        for r in db_select("thirumana_mandapam"):
            with st.expander(f"👤 {r['name']} | ₹{r.get('amount',0)}"):
                for l,k in [("Name","name"),("Address","address"),("Bond","bond_no"),("Date","bond_issued_date"),("Amount","amount")]:
                    st.write(f"**{l}:** {r.get(k,'N/A')}")
                if st.button("🗑️",key=f"dt_{r['id']}"): db_delete("thirumana_mandapam","id",r['id']); st.rerun()


# ============================================================
# SIDEBAR
# ============================================================
def render_sidebar():
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align:center;padding:12px;background:linear-gradient(135deg,#ff6b35,#f7c948);border-radius:10px;margin-bottom:12px;">
            <h2 style="color:#8B0000;margin:0;">🛕</h2>
            <p style="color:#5a1a00;margin:2px 0 0 0;font-weight:600;font-size:0.7em;">Sree Bhadreshwari Amman<br>Temple Management</p>
        </div>
        <div style="color:#ccc;padding:5px 10px;font-size:0.8em;">👤 <b style="color:#f7c948">{st.session_state.username}</b> ({st.session_state.user_role})</div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        pages=[("🏠 Dashboard","Dashboard"),("👥 Devotees","Devotees"),("🧾 Billing","Billing"),
               ("💸 Expenses","Expenses"),("📊 Reports","Reports"),("🏷️ Assets","Assets"),
               ("📚 Samaya Vakuppu","Samaya"),("💒 Thirumana","Thirumana"),
               ("⚙️ Settings","Settings"),("👥 Users","Users")]
        for l,p in pages:
            if p=="Users" and st.session_state.user_role!='admin': continue
            if st.button(l,key=f"n_{p}",use_container_width=True):
                st.session_state.current_page=p; st.rerun()

        st.markdown("---")
        if st.button("🚪 Logout",key="lo",use_container_width=True):
            for k in defaults: st.session_state[k]=defaults[k]
            st.rerun()

        st.markdown('<div style="text-align:center;padding:15px 0;color:#555;font-size:0.65em;">v2.0 🙏 அம்மே நாராயணா 🙏</div>', unsafe_allow_html=True)


# ============================================================
# MAIN
# ============================================================
def main():
    if not st.session_state.logged_in:
        page_login()
    else:
        render_sidebar()
        pm={"Dashboard":page_dashboard,"Devotees":page_devotee_enrollment,
            "Billing":page_billing,"Expenses":page_expenses,"Reports":page_reports,
            "Assets":page_assets,"Samaya":page_samaya,"Thirumana":page_thirumana,
            "Settings":page_settings,"Users":page_users}
        c=st.session_state.current_page
        pm.get(c,page_dashboard)()

if __name__ == "__main__":
    main()
