import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import uuid
import base64
import time
import json

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
# CONSTANTS
# ============================================================
NATCHATHIRAM_LIST = [
    "அசுவினி (Ashwini)", "பரணி (Bharani)", "கார்த்திகை (Karthigai)",
    "ரோகிணி (Rohini)", "மிருகசீரிடம் (Mrigashirsha)", "திருவாதிரை (Thiruvadirai)",
    "புனர்பூசம் (Punarvasu)", "பூசம் (Pushya)", "ஆயில்யம் (Ashlesha)",
    "மகம் (Magha)", "பூரம் (Purva Phalguni)", "உத்திரம் (Uttara Phalguni)",
    "அஸ்தம் (Hasta)", "சித்திரை (Chitra)", "சுவாதி (Swati)",
    "விசாகம் (Vishakha)", "அனுஷம் (Anuradha)", "கேட்டை (Jyeshtha)",
    "மூலம் (Mula)", "பூராடம் (Purva Ashadha)", "உத்திராடம் (Uttara Ashadha)",
    "திருவோணம் (Shravana)", "அவிட்டம் (Dhanishta)", "சதயம் (Shatabhisha)",
    "பூரட்டாதி (Purva Bhadrapada)", "உத்திரட்டாதி (Uttara Bhadrapada)",
    "ரேவதி (Revati)"
]

RELATION_TYPES = [
    "Self", "Spouse", "Son", "Daughter", "Father", "Mother",
    "Brother", "Sister", "Grandfather", "Grandmother",
    "Father-in-law", "Mother-in-law", "Son-in-law",
    "Daughter-in-law", "Uncle", "Aunt", "Nephew", "Niece", "Other"
]

# Date range constants
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
        position: relative;
        padding: 30px;
        border-radius: 20px;
        backdrop-filter: blur(10px);
        background: rgba(255,255,255,0.92);
        box-shadow: 0 8px 32px rgba(0,0,0,0.15);
        border: 1px solid rgba(255,107,53,0.2);
    }
    
    .login-bg {
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        z-index: -1;
        background: linear-gradient(135deg, #fff5ee 0%, #ffe4c4 30%, #ffdab9 60%, #fff5ee 100%);
    }
    
    .amman-photo-container {
        text-align: center;
        margin-bottom: 15px;
    }
    .amman-photo {
        width: 130px; height: 130px;
        border-radius: 50%;
        object-fit: cover;
        border: 4px solid #ff6b35;
        box-shadow: 0 4px 20px rgba(255,107,53,0.4),
                    0 0 30px rgba(247,201,72,0.3);
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
        white-space: nowrap; margin: 10px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.2);
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
    .bill-preview {
        background: #fffdf7; padding: 30px; border: 2px solid #ff6b35;
        border-radius: 15px; max-width: 550px; margin: 20px auto;
    }
    .bill-header {
        text-align: center; border-bottom: 2px solid #ff6b35; padding-bottom: 15px;
    }
    .success-box {
        background: #d4edda; border: 1px solid #c3e6cb; padding: 15px;
        border-radius: 10px; color: #155724; margin: 10px 0;
    }
    
    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    div[data-testid="stSidebar"] .stButton > button {
        width: 100%; text-align: left; background: transparent;
        color: #f0f0f0; border: 1px solid rgba(255,255,255,0.1);
        border-radius: 8px; margin: 2px 0; padding: 8px 15px;
        transition: all 0.3s ease;
    }
    div[data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255,107,53,0.3); border-color: #ff6b35;
    }
    
    .temple-name-login {
        color: #8B0000;
        font-size: 1.5em;
        font-weight: 700;
        text-align: center;
        margin: 10px 0;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    .tamil-text {
        color: #c0392b;
        font-size: 1.1em;
        font-weight: 600;
        text-align: center;
        margin: 5px 0 15px 0;
    }
    
    .login-footer {
        text-align: center;
        margin-top: 15px;
        color: #888;
        font-size: 0.8em;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE
# ============================================================
defaults = {
    'logged_in': False, 'username': '', 'user_role': '',
    'current_page': 'Dashboard', 'bg_image_base64': None,
    'amman_photo_base64': None
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ============================================================
# DATABASE HELPER FUNCTIONS
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
        st.error(f"DB Select Error on {table}: {e}")
        return []

def db_insert(table, data):
    try:
        result = supabase.table(table).insert(data).execute()
        return result.data if result.data else None
    except Exception as e:
        st.error(f"DB Insert Error on {table}: {e}")
        return None

def db_update(table, data, match_col, match_val):
    try:
        result = supabase.table(table).update(data).eq(match_col, match_val).execute()
        return result.data if result.data else None
    except Exception as e:
        st.error(f"DB Update Error on {table}: {e}")
        return None

def db_delete(table, match_col, match_val):
    try:
        supabase.table(table).delete().eq(match_col, match_val).execute()
        return True
    except Exception as e:
        st.error(f"DB Delete Error on {table}: {e}")
        return False

def file_to_base64(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        encoded = base64.b64encode(bytes_data).decode()
        return f"data:{uploaded_file.type};base64,{encoded}"
    return None

def get_income(start, end):
    bills = db_select("bills", "amount", gte_filters={"bill_date": start}, lte_filters={"bill_date": end})
    return sum(float(b.get('amount', 0)) for b in bills)

def get_expense(start, end):
    exps = db_select("expenses", "amount", gte_filters={"expense_date": start}, lte_filters={"expense_date": end})
    return sum(float(e.get('amount', 0)) for e in exps)

def get_period_dates(period):
    today = date.today()
    if period == "Daily":
        return today, today
    elif period == "Weekly":
        return today - timedelta(days=today.weekday()), today
    elif period == "Monthly":
        return today.replace(day=1), today
    elif period == "Yearly":
        return today.replace(month=1, day=1), today
    return today, today

def get_todays_birthdays():
    today = date.today()
    bdays = []
    for d in db_select("devotees", "name, dob"):
        if d.get('dob'):
            try:
                dob = datetime.strptime(str(d['dob']), '%Y-%m-%d').date()
                if dob.month == today.month and dob.day == today.day:
                    bdays.append(f"🎂 {d['name']} (Devotee)")
            except:
                pass
    for m in db_select("family_members", "name, dob"):
        if m.get('dob'):
            try:
                dob = datetime.strptime(str(m['dob']), '%Y-%m-%d').date()
                if dob.month == today.month and dob.day == today.day:
                    bdays.append(f"🎂 {m['name']} (Family)")
            except:
                pass
    return bdays

def gen_bill_no():
    return f"TMS-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:4].upper()}"


# ============================================================
# DEFAULT AMMAN PHOTO (Placeholder SVG as base64)
# ============================================================
DEFAULT_AMMAN_SVG = """data:image/svg+xml;base64,""" + base64.b64encode("""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="200" height="200">
  <defs>
    <radialGradient id="bg" cx="50%" cy="50%" r="50%">
      <stop offset="0%" style="stop-color:#fff5ee"/>
      <stop offset="100%" style="stop-color:#ffdab9"/>
    </radialGradient>
  </defs>
  <circle cx="100" cy="100" r="98" fill="url(#bg)" stroke="#ff6b35" stroke-width="3"/>
  <text x="100" y="80" text-anchor="middle" font-size="50">🙏</text>
  <text x="100" y="120" text-anchor="middle" font-size="14" fill="#8B0000" font-weight="bold">ஸ்ரீ</text>
  <text x="100" y="140" text-anchor="middle" font-size="11" fill="#8B0000" font-weight="bold">பத்ரேஸ்வரி</text>
  <text x="100" y="158" text-anchor="middle" font-size="11" fill="#8B0000" font-weight="bold">அம்மன்</text>
</svg>
""".strip().encode()).decode()


# ============================================================
# PAGE: LOGIN
# ============================================================
def page_login():
    # Background
    bg_css = ""
    if st.session_state.get('bg_image_base64'):
        bg_css = f"""
        <style>
            .stApp {{
                background-image: url('{st.session_state.bg_image_base64}');
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
            }}
        </style>
        """
    else:
        bg_css = """
        <style>
            .stApp {
                background: linear-gradient(135deg, #fff5ee 0%, #ffe4c4 25%, #ffdab9 50%, #ffe4c4 75%, #fff5ee 100%);
            }
        </style>
        """
    st.markdown(bg_css, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        # Amman Photo in Round
        amman_photo = st.session_state.get('amman_photo_base64') or DEFAULT_AMMAN_SVG
        st.markdown(f"""
        <div class="amman-photo-container">
            <img src="{amman_photo}" class="amman-photo" alt="Amman">
        </div>
        """, unsafe_allow_html=True)
        
        # Temple Name
        st.markdown("""
        <div class="temple-name-login">
            🛕 Sree Bhadreshwari Amman Temple<br>Management System
        </div>
        <div class="tamil-text">
            🙏 அம்மே நாராயணா ..தேவி நாராயணா 🙏
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="Enter your username")
            password = st.text_input("🔑 Password", type="password", placeholder="Enter your password")
            col_a, col_b, col_c = st.columns([1, 2, 1])
            with col_b:
                submitted = st.form_submit_button("🚀 Login", use_container_width=True)
            
            if submitted:
                if not username or not password:
                    st.warning("⚠️ Please enter both username and password!")
                elif not DB_CONNECTED:
                    st.error("❌ Database not connected! Check Supabase credentials.")
                else:
                    users = db_select("users", filters={"username": username})
                    if users and users[0].get('password_hash') == password:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.user_role = users[0].get('role', 'user')
                        st.success("✅ Login successful!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password!")
        
        # Upload options for login page customization
        with st.expander("🎨 Customize Login Page"):
            amman_upload = st.file_uploader("Upload Amman Photo (Round Display)", type=['jpg', 'jpeg', 'png'], key="amman_up")
            if amman_upload:
                st.session_state.amman_photo_base64 = file_to_base64(amman_upload)
                st.success("✅ Amman photo updated!")
                st.rerun()
            
            bg_upload = st.file_uploader("Upload Background Image", type=['jpg', 'jpeg', 'png'], key="bg_up")
            if bg_upload:
                st.session_state.bg_image_base64 = file_to_base64(bg_upload)
                st.success("✅ Background image updated!")
                st.rerun()
            
            if st.button("🔄 Reset to Default"):
                st.session_state.amman_photo_base64 = None
                st.session_state.bg_image_base64 = None
                st.rerun()
        
        st.markdown("""
        <div class="login-footer">
            Default Login: admin / admin123
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# PAGE: DASHBOARD
# ============================================================
def page_dashboard():
    st.markdown("""
    <div class="main-header">
        <h1>🛕 Sree Bhadreshwari Amman Temple</h1>
        <p>🙏 அம்மே நாராயணா ..தேவி நாராயணா 🙏</p>
    </div>
    """, unsafe_allow_html=True)
    
    # News Ticker
    ticker_parts = []
    birthdays = get_todays_birthdays()
    if birthdays:
        ticker_parts.extend(birthdays)
    news = db_select("news_ticker", filters={"is_active": True})
    for n in news:
        ticker_parts.append(f"📢 {n['message']}")
    if not ticker_parts:
        ticker_parts.append("🛕 Welcome to Sree Bhadreshwari Amman Temple Management System! 🙏 அம்மே நாராயணா 🙏")
    
    ticker_str = " &nbsp;&nbsp; ⭐ &nbsp;&nbsp; ".join(ticker_parts)
    st.markdown(f"""
    <div class="news-ticker-wrapper">
        <div class="news-ticker-text">{ticker_str}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Period Selector
    st.markdown("")
    period = st.selectbox("📅 Select Period", ["Daily", "Weekly", "Monthly", "Yearly"])
    start_dt, end_dt = get_period_dates(period)
    
    income = get_income(start_dt, end_dt)
    expense = get_expense(start_dt, end_dt)
    balance = income - expense
    total_devotees = len(db_select("devotees", "id"))
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-card income"><h3>💰 {period} Income</h3><h2>₹ {income:,.2f}</h2></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card expense"><h3>💸 {period} Expenses</h3><h2>₹ {expense:,.2f}</h2></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card balance"><h3>💎 {period} Balance</h3><h2>₹ {balance:,.2f}</h2></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric-card info"><h3>👥 Total Devotees</h3><h2>{total_devotees}</h2></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("### 🎂 Today's Birthdays")
        if birthdays:
            for b in birthdays:
                st.markdown(f'<div class="birthday-card">🎉 {b} - Happy Birthday! 🎈</div>', unsafe_allow_html=True)
        else:
            st.info("No birthdays today 📅")
    
    with col_right:
        st.markdown("### 🙏 Today's Pooja Schedule")
        today_poojas = db_select("daily_pooja", filters={"pooja_date": str(date.today())})
        if today_poojas:
            for p in today_poojas:
                icon = "✅" if p.get('status') == 'completed' else "⏳"
                st.markdown(f'<div class="pooja-card">{icon} <strong>{p["pooja_name"]}</strong> — {p.get("pooja_time", "N/A")}</div>', unsafe_allow_html=True)
                if p.get('status') != 'completed':
                    if st.button(f"Mark Complete", key=f"comp_{p['id']}"):
                        db_update("daily_pooja", {"status": "completed"}, "id", p['id'])
                        st.rerun()
        else:
            st.info("No pooja scheduled today")
        
        with st.expander("➕ Add Daily Pooja"):
            with st.form("add_dp"):
                dp_name = st.text_input("Pooja Name", key="dp_n")
                dp_time = st.text_input("Time (e.g. 6:00 AM)", key="dp_t")
                dp_date = st.date_input("Date", value=date.today(), key="dp_d")
                if st.form_submit_button("Add"):
                    if dp_name:
                        db_insert("daily_pooja", {
                            "pooja_name": dp_name, "pooja_time": dp_time,
                            "pooja_date": str(dp_date), "status": "pending"
                        })
                        st.success("✅ Added!")
                        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📊 Income vs Expenses")
    chart_df = pd.DataFrame({"Category": ["Income", "Expenses", "Balance"], "Amount (₹)": [income, expense, balance]})
    st.bar_chart(chart_df.set_index("Category"))


# ============================================================
# PAGE: DEVOTEE ENROLLMENT
# ============================================================
def page_devotee_enrollment():
    st.markdown("""
    <div class="main-header">
        <h1>👥 Devotee Enrollment</h1>
        <p>Register family head, family members & yearly poojas</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["➕ New Enrollment", "🔍 Search & Manage", "👨‍👩‍👧‍👦 Family Members"])
    
    with tab1:
        st.markdown("### 👤 Family Head Registration")
        with st.form("enroll_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("👤 Full Name *", placeholder="Enter full name")
                dob = st.date_input("📅 Date of Birth", value=date(1990, 1, 1),
                                    min_value=MIN_DATE, max_value=MAX_DATE)
                relation_type = st.selectbox("👪 Relation Type", RELATION_TYPES)
                mobile_no = st.text_input("📱 Mobile Number")
                whatsapp_no = st.text_input("📲 WhatsApp Number")
            with c2:
                wedding_day = st.date_input("💒 Wedding Day", value=None,
                                            min_value=MIN_DATE, max_value=MAX_DATE)
                natchathiram = st.selectbox("⭐ Natchathiram", ["-- Select --"] + NATCHATHIRAM_LIST)
                address = st.text_area("🏠 Address", height=100)
                photo = st.file_uploader("📷 Upload Photo", type=['jpg', 'jpeg', 'png'])
            
            st.markdown("#### 🙏 Yearly Pooja (Optional)")
            yc1, yc2, yc3 = st.columns(3)
            pt_list = [p['name'] for p in db_select("pooja_types", "name")]
            with yc1:
                yp_type = st.selectbox("Pooja Type", ["-- Select --"] + pt_list, key="yp1_t")
            with yc2:
                yp_date = st.date_input("Pooja Date", key="yp1_d",
                                        min_value=MIN_DATE, max_value=MAX_DATE)
            with yc3:
                yp_desc = st.text_input("Description", key="yp1_desc")
            
            if st.form_submit_button("✅ Register Devotee", use_container_width=True):
                if not name.strip():
                    st.error("❌ Name is required!")
                else:
                    photo_url = file_to_base64(photo)
                    result = db_insert("devotees", {
                        "name": name.strip(), "dob": str(dob),
                        "relation_type": relation_type, "mobile_no": mobile_no,
                        "whatsapp_no": whatsapp_no,
                        "wedding_day": str(wedding_day) if wedding_day else None,
                        "natchathiram": natchathiram if natchathiram != "-- Select --" else None,
                        "address": address, "photo_url": photo_url
                    })
                    if result:
                        if yp_type != "-- Select --":
                            db_insert("devotee_yearly_pooja", {
                                "devotee_id": result[0]['id'], "pooja_type": yp_type,
                                "pooja_date": str(yp_date), "description": yp_desc
                            })
                        st.success(f"✅ '{name}' enrolled successfully!")
                        st.rerun()
    
    with tab2:
        st.markdown("### 🔍 Search Devotees")
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            s_name = st.text_input("Search by Name", key="sn")
        with sc2:
            s_mobile = st.text_input("Search by Mobile", key="sm")
        with sc3:
            s_address = st.text_input("Search by Address", key="sa")
        
        devotees = db_select("devotees")
        if s_name:
            devotees = [d for d in devotees if s_name.lower() in d.get('name', '').lower()]
        if s_mobile:
            devotees = [d for d in devotees if s_mobile in d.get('mobile_no', '')]
        if s_address:
            devotees = [d for d in devotees if s_address.lower() in d.get('address', '').lower()]
        
        st.markdown(f"**Found: {len(devotees)} devotee(s)**")
        
        for dev in devotees:
            with st.expander(f"👤 {dev['name']} | 📱 {dev.get('mobile_no','N/A')} | ⭐ {dev.get('natchathiram','N/A')}"):
                dc1, dc2 = st.columns([3, 1])
                with dc1:
                    st.write(f"**Name:** {dev['name']}")
                    st.write(f"**DOB:** {dev.get('dob', 'N/A')}")
                    st.write(f"**Mobile:** {dev.get('mobile_no', 'N/A')}")
                    st.write(f"**WhatsApp:** {dev.get('whatsapp_no', 'N/A')}")
                    st.write(f"**Relation:** {dev.get('relation_type', 'N/A')}")
                    st.write(f"**Wedding Day:** {dev.get('wedding_day', 'N/A')}")
                    st.write(f"**Natchathiram:** {dev.get('natchathiram', 'N/A')}")
                    st.write(f"**Address:** {dev.get('address', 'N/A')}")
                with dc2:
                    if dev.get('photo_url') and dev['photo_url'].startswith('data:'):
                        st.markdown(f'<img src="{dev["photo_url"]}" width="130" style="border-radius:10px;">', unsafe_allow_html=True)
                
                # Yearly Poojas
                st.markdown("**🙏 Yearly Poojas:**")
                y_poojas = db_select("devotee_yearly_pooja", filters={"devotee_id": dev['id']})
                if y_poojas:
                    for yp in y_poojas:
                        ypc1, ypc2 = st.columns([5, 1])
                        with ypc1:
                            st.write(f"  • {yp['pooja_type']} — {yp.get('pooja_date','N/A')} — {yp.get('description','')}")
                        with ypc2:
                            if st.button("❌", key=f"dyp_{yp['id']}"):
                                db_delete("devotee_yearly_pooja", "id", yp['id'])
                                st.rerun()
                else:
                    st.write("  No yearly poojas.")
                
                with st.form(f"ayp_{dev['id']}"):
                    st.markdown("**➕ Add Yearly Pooja**")
                    ayc1, ayc2, ayc3 = st.columns(3)
                    pt_names = [p['name'] for p in db_select("pooja_types", "name")]
                    with ayc1:
                        new_ypt = st.selectbox("Type", ["-- Select --"] + pt_names, key=f"nypt_{dev['id']}")
                    with ayc2:
                        new_ypd = st.date_input("Date", key=f"nypd_{dev['id']}",
                                                min_value=MIN_DATE, max_value=MAX_DATE)
                    with ayc3:
                        new_ypdesc = st.text_input("Desc", key=f"nypdc_{dev['id']}")
                    if st.form_submit_button("Add Pooja"):
                        if new_ypt != "-- Select --":
                            db_insert("devotee_yearly_pooja", {
                                "devotee_id": dev['id'], "pooja_type": new_ypt,
                                "pooja_date": str(new_ypd), "description": new_ypdesc
                            })
                            st.success("✅ Added!")
                            st.rerun()
                
                st.markdown("---")
                edc1, edc2 = st.columns(2)
                with edc1:
                    if st.button("✏️ Edit", key=f"edit_{dev['id']}"):
                        st.session_state[f"editing_{dev['id']}"] = not st.session_state.get(f"editing_{dev['id']}", False)
                        st.rerun()
                with edc2:
                    if st.button("🗑️ Delete", key=f"del_{dev['id']}"):
                        db_delete("devotee_yearly_pooja", "devotee_id", dev['id'])
                        db_delete("family_members", "devotee_id", dev['id'])
                        db_delete("devotees", "id", dev['id'])
                        st.success(f"✅ '{dev['name']}' deleted!")
                        st.rerun()
                
                if st.session_state.get(f"editing_{dev['id']}", False):
                    with st.form(f"ef_{dev['id']}"):
                        st.markdown("### ✏️ Edit")
                        ec1, ec2 = st.columns(2)
                        with ec1:
                            e_name = st.text_input("Name", value=dev.get('name', ''), key=f"en_{dev['id']}")
                            e_dob_val = date(1990, 1, 1)
                            if dev.get('dob'):
                                try:
                                    e_dob_val = datetime.strptime(str(dev['dob']), '%Y-%m-%d').date()
                                except:
                                    pass
                            e_dob = st.date_input("DOB", value=e_dob_val, key=f"ed_{dev['id']}",
                                                  min_value=MIN_DATE, max_value=MAX_DATE)
                            e_mob = st.text_input("Mobile", value=dev.get('mobile_no', ''), key=f"em_{dev['id']}")
                            e_wa = st.text_input("WhatsApp", value=dev.get('whatsapp_no', ''), key=f"ew_{dev['id']}")
                        with ec2:
                            e_rel = st.selectbox("Relation", RELATION_TYPES,
                                index=RELATION_TYPES.index(dev['relation_type']) if dev.get('relation_type') in RELATION_TYPES else 0,
                                key=f"er_{dev['id']}")
                            star_opts = ["-- Select --"] + NATCHATHIRAM_LIST
                            curr_star = dev.get('natchathiram', '-- Select --')
                            e_star = st.selectbox("Natchathiram", star_opts,
                                index=star_opts.index(curr_star) if curr_star in star_opts else 0,
                                key=f"es_{dev['id']}")
                            e_addr = st.text_area("Address", value=dev.get('address', ''), key=f"ea_{dev['id']}")
                            e_wed_val = None
                            if dev.get('wedding_day'):
                                try:
                                    e_wed_val = datetime.strptime(str(dev['wedding_day']), '%Y-%m-%d').date()
                                except:
                                    e_wed_val = None
                            e_wed = st.date_input("Wedding Day", value=e_wed_val, key=f"ewedd_{dev['id']}",
                                                  min_value=MIN_DATE, max_value=MAX_DATE)
                        
                        if st.form_submit_button("💾 Save"):
                            db_update("devotees", {
                                "name": e_name, "dob": str(e_dob),
                                "mobile_no": e_mob, "whatsapp_no": e_wa,
                                "relation_type": e_rel,
                                "natchathiram": e_star if e_star != "-- Select --" else None,
                                "address": e_addr,
                                "wedding_day": str(e_wed) if e_wed else None
                            }, "id", dev['id'])
                            st.session_state[f"editing_{dev['id']}"] = False
                            st.success("✅ Updated!")
                            st.rerun()
    
    with tab3:
        st.markdown("### 👨‍👩‍👧‍👦 Manage Family Members")
        devs = db_select("devotees", "id, name, mobile_no")
        if not devs:
            st.info("No devotees enrolled.")
            return
        
        dev_opts = {f"{d['name']} ({d.get('mobile_no','N/A')})": d['id'] for d in devs}
        sel_head = st.selectbox("Select Family Head", list(dev_opts.keys()))
        head_id = dev_opts[sel_head]
        
        members = db_select("family_members", filters={"devotee_id": head_id})
        if members:
            st.markdown("**Current Members:**")
            for fm in members:
                fmc1, fmc2 = st.columns([5, 1])
                with fmc1:
                    st.write(f"👤 **{fm['name']}** | {fm.get('relation_type','N/A')} | DOB: {fm.get('dob','N/A')} | ⭐ {fm.get('natchathiram','N/A')}")
                with fmc2:
                    if st.button("🗑️", key=f"dfm_{fm['id']}"):
                        db_delete("family_members", "id", fm['id'])
                        st.rerun()
        
        st.markdown("---")
        st.markdown("### ➕ Add Family Member")
        with st.form("add_fm", clear_on_submit=True):
            fc1, fc2 = st.columns(2)
            with fc1:
                fm_name = st.text_input("👤 Name *")
                fm_dob = st.date_input("📅 DOB", value=date(1995, 1, 1),
                                       min_value=MIN_DATE, max_value=MAX_DATE)
                fm_rel = st.selectbox("👪 Relation", RELATION_TYPES)
            with fc2:
                fm_wed = st.date_input("💒 Wedding Day", value=None, key="fmw",
                                       min_value=MIN_DATE, max_value=MAX_DATE)
                fm_star = st.selectbox("⭐ Natchathiram", ["-- Select --"] + NATCHATHIRAM_LIST, key="fms")
            
            if st.form_submit_button("➕ Add Member", use_container_width=True):
                if fm_name.strip():
                    db_insert("family_members", {
                        "devotee_id": head_id, "name": fm_name.strip(),
                        "dob": str(fm_dob), "relation_type": fm_rel,
                        "wedding_day": str(fm_wed) if fm_wed else None,
                        "natchathiram": fm_star if fm_star != "-- Select --" else None
                    })
                    st.success(f"✅ '{fm_name}' added!")
                    st.rerun()
                else:
                    st.error("❌ Name required!")


# ============================================================
# PAGE: BILLING
# ============================================================
def page_billing():
    st.markdown("""
    <div class="main-header">
        <h1>🧾 Billing</h1>
        <p>Generate pooja bills for devotees</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["➕ New Bill", "📋 Bill History"])
    
    with tab1:
        dev_type = st.radio("Devotee Type", ["Enrolled Devotee", "Guest Devotee"], horizontal=True)
        bc1, bc2 = st.columns(2)
        
        with bc1:
            manual_bill = st.text_input("📝 Manual Bill No")
            bill_book = st.text_input("📖 Bill Book No")
            pt_data = db_select("pooja_types")
            pt_opts = {f"{p['name']} — ₹{p.get('amount',0)}": p for p in pt_data} if pt_data else {}
            sel_pooja = st.selectbox("🙏 Pooja Type", list(pt_opts.keys()) if pt_opts else ["No pooja types"])
            default_amt = float(pt_opts[sel_pooja].get('amount', 0)) if sel_pooja in pt_opts else 0.0
            amount = st.number_input("💰 Amount (₹)", value=default_amt, min_value=0.0, step=10.0)
            bill_date = st.date_input("📅 Bill Date", value=date.today())
        
        with bc2:
            devotee_id = None
            g_name = g_addr = g_mob = g_wa = ""
            
            if dev_type == "Enrolled Devotee":
                st.markdown("### 🔍 Search Enrolled Devotee")
                search_by = st.selectbox("Search By", ["Name", "Mobile", "WhatsApp", "Address"])
                search_val = st.text_input(f"Enter {search_by}")
                all_devs = db_select("devotees")
                if search_val:
                    field_map = {"Name": "name", "Mobile": "mobile_no", "WhatsApp": "whatsapp_no", "Address": "address"}
                    field = field_map[search_by]
                    all_devs = [d for d in all_devs if search_val.lower() in str(d.get(field, '')).lower()]
                if all_devs:
                    dev_map = {f"{d['name']} — {d.get('mobile_no','N/A')} — {str(d.get('address',''))[:30]}": d for d in all_devs}
                    chosen = st.selectbox("Select Devotee", list(dev_map.keys()))
                    if chosen:
                        sd = dev_map[chosen]
                        devotee_id = sd['id']
                        st.markdown(f"""
                        <div class="success-box">
                            👤 <strong>{sd['name']}</strong><br>
                            📱 {sd.get('mobile_no','N/A')} &nbsp; 📲 {sd.get('whatsapp_no','N/A')}<br>
                            🏠 {sd.get('address','N/A')}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.warning("No devotees match")
            else:
                st.markdown("### 👤 Guest Details")
                g_name = st.text_input("👤 Guest Name *")
                g_addr = st.text_area("🏠 Address *", height=80)
                g_mob = st.text_input("📱 Mobile")
                g_wa = st.text_input("📲 WhatsApp")
        
        if st.button("🧾 Generate Bill", use_container_width=True, type="primary"):
            valid = True
            if dev_type == "Enrolled Devotee" and not devotee_id:
                st.error("❌ Select a devotee!"); valid = False
            if dev_type == "Guest Devotee" and not g_name.strip():
                st.error("❌ Guest name required!"); valid = False
            if amount <= 0:
                st.error("❌ Amount > 0!"); valid = False
            
            if valid:
                bill_no = gen_bill_no()
                pooja_name = sel_pooja.split(" — ")[0] if " — " in sel_pooja else sel_pooja
                bill_data = {
                    "bill_no": bill_no, "manual_bill_no": manual_bill,
                    "bill_book_no": bill_book,
                    "devotee_type": "enrolled" if dev_type == "Enrolled Devotee" else "guest",
                    "devotee_id": devotee_id,
                    "guest_name": g_name if dev_type == "Guest Devotee" else None,
                    "guest_address": g_addr if dev_type == "Guest Devotee" else None,
                    "guest_mobile": g_mob if dev_type == "Guest Devotee" else None,
                    "guest_whatsapp": g_wa if dev_type == "Guest Devotee" else None,
                    "pooja_type": pooja_name, "amount": amount, "bill_date": str(bill_date)
                }
                res = db_insert("bills", bill_data)
                if res:
                    st.success(f"✅ Bill: {bill_no}")
                    if dev_type == "Enrolled Devotee" and devotee_id:
                        di = db_select("devotees", filters={"id": devotee_id})
                        b_name = di[0]['name'] if di else "N/A"
                        b_addr = di[0].get('address', '') if di else ""
                        b_mob = di[0].get('mobile_no', '') if di else ""
                    else:
                        b_name, b_addr, b_mob = g_name, g_addr, g_mob
                    
                    st.markdown(f"""
                    <div class="bill-preview">
                        <div class="bill-header">
                            <h2 style="color:#8B0000; margin:0;">🛕 Sree Bhadreshwari Amman Temple</h2>
                            <p style="margin:3px 0;">🙏 அம்மே நாராயணா 🙏</p>
                        </div>
                        <div style="padding:15px 0;">
                            <table style="width:100%;">
                                <tr><td><strong>Bill No:</strong></td><td>{bill_no}</td></tr>
                                <tr><td><strong>Manual Bill:</strong></td><td>{manual_bill}</td></tr>
                                <tr><td><strong>Book No:</strong></td><td>{bill_book}</td></tr>
                                <tr><td><strong>Date:</strong></td><td>{bill_date}</td></tr>
                                <tr><td colspan="2"><hr style="border:1px dashed #ccc;"></td></tr>
                                <tr><td><strong>Name:</strong></td><td>{b_name}</td></tr>
                                <tr><td><strong>Address:</strong></td><td>{b_addr}</td></tr>
                                <tr><td><strong>Mobile:</strong></td><td>{b_mob}</td></tr>
                                <tr><td colspan="2"><hr style="border:1px dashed #ccc;"></td></tr>
                                <tr><td><strong>Pooja:</strong></td><td>{pooja_name}</td></tr>
                                <tr><td><strong>Amount:</strong></td><td style="font-size:1.4em; color:#11998e;"><strong>₹ {amount:,.2f}</strong></td></tr>
                            </table>
                        </div>
                        <div style="text-align:center; border-top:2px solid #ff6b35; padding-top:10px;">
                            <p style="margin:0; color:#666;">🙏 அம்மே நாராயணா ..தேவி நாராயணா 🙏</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### 📋 Bill History")
        bills = db_select("bills")
        bills = sorted(bills, key=lambda x: x.get('created_at', ''), reverse=True)
        if bills:
            for b in bills:
                bname = b.get('guest_name', '')
                if b.get('devotee_type') == 'enrolled' and b.get('devotee_id'):
                    dd = db_select("devotees", "name", filters={"id": b['devotee_id']})
                    bname = dd[0]['name'] if dd else 'Unknown'
                with st.expander(f"🧾 {b.get('bill_no','')} | {bname} | {b.get('pooja_type','')} | ₹{b.get('amount',0)} | {b.get('bill_date','')}"):
                    st.write(f"**Bill No:** {b.get('bill_no','')}")
                    st.write(f"**Manual:** {b.get('manual_bill_no','')}")
                    st.write(f"**Book:** {b.get('bill_book_no','')}")
                    st.write(f"**Pooja:** {b.get('pooja_type','')} | **Amount:** ₹{b.get('amount',0):,.2f}")
                    st.write(f"**Date:** {b.get('bill_date','')}")
                    if b.get('guest_name'):
                        st.write(f"**Guest:** {b['guest_name']} | {b.get('guest_address','')} | 📱{b.get('guest_mobile','')}")
                    if st.session_state.user_role == 'admin':
                        if st.button("🗑️ Delete", key=f"dbill_{b['id']}"):
                            db_delete("bills", "id", b['id'])
                            st.success("Deleted!"); st.rerun()
        else:
            st.info("No bills")


# ============================================================
# PAGE: EXPENSES
# ============================================================
def page_expenses():
    st.markdown("""
    <div class="main-header">
        <h1>💸 Expenses</h1>
        <p>Track temple expenses</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["➕ Add Expense", "📋 History"])
    
    with tab1:
        with st.form("exp_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                et_data = db_select("expense_types", "name")
                et_names = [e['name'] for e in et_data] if et_data else ["Miscellaneous"]
                exp_type = st.selectbox("📂 Expense Type", et_names)
                exp_amt = st.number_input("💰 Amount (₹)", min_value=0.0, step=10.0)
            with c2:
                exp_date = st.date_input("📅 Date", value=date.today())
                exp_desc = st.text_area("📝 Description", height=100)
            if st.form_submit_button("💾 Save", use_container_width=True):
                if exp_amt > 0:
                    db_insert("expenses", {"expense_type": exp_type, "amount": exp_amt,
                                           "description": exp_desc, "expense_date": str(exp_date)})
                    st.success("✅ Saved!"); st.rerun()
                else:
                    st.error("❌ Amount > 0!")
    
    with tab2:
        exps = sorted(db_select("expenses"), key=lambda x: x.get('expense_date', ''), reverse=True)
        if exps:
            total = sum(float(e.get('amount', 0)) for e in exps)
            st.metric("Total", f"₹ {total:,.2f}")
            df = pd.DataFrame([{"Date": e.get('expense_date',''), "Type": e.get('expense_type',''),
                                "Amount": f"₹ {float(e.get('amount',0)):,.2f}", "Desc": e.get('description','')} for e in exps])
            st.dataframe(df, use_container_width=True, hide_index=True)
            if st.session_state.user_role == 'admin':
                exp_opts = {f"{e.get('expense_date','')} — {e.get('expense_type','')} — ₹{e.get('amount',0)}": e['id'] for e in exps}
                sel = st.selectbox("Delete", list(exp_opts.keys()))
                if st.button("🗑️ Delete"):
                    db_delete("expenses", "id", exp_opts[sel]); st.success("Deleted!"); st.rerun()
        else:
            st.info("No expenses")


# ============================================================
# PAGE: REPORTS
# ============================================================
def page_reports():
    st.markdown("""
    <div class="main-header">
        <h1>📊 Reports</h1>
        <p>Financial reports with filters</p>
    </div>
    """, unsafe_allow_html=True)
    
    rc1, rc2, rc3 = st.columns(3)
    with rc1:
        period = st.selectbox("📅 Period", ["Daily", "Weekly", "Monthly", "Yearly", "Custom Date"])
    
    today = date.today()
    if period == "Custom Date":
        with rc2:
            start_dt = st.date_input("From", value=today - timedelta(days=30))
        with rc3:
            end_dt = st.date_input("To", value=today)
    else:
        start_dt, end_dt = get_period_dates(period)
    
    pt_names = ["All"] + [p['name'] for p in db_select("pooja_types", "name")]
    pooja_filter = st.selectbox("🙏 Pooja Filter", pt_names)
    
    bills = db_select("bills", gte_filters={"bill_date": start_dt}, lte_filters={"bill_date": end_dt})
    expenses = db_select("expenses", gte_filters={"expense_date": start_dt}, lte_filters={"expense_date": end_dt})
    if pooja_filter != "All":
        bills = [b for b in bills if b.get('pooja_type') == pooja_filter]
    
    ti = sum(float(b.get('amount', 0)) for b in bills)
    te = sum(float(e.get('amount', 0)) for e in expenses)
    net = ti - te
    
    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        st.markdown(f'<div class="metric-card income"><h3>💰 Income</h3><h2>₹ {ti:,.2f}</h2></div>', unsafe_allow_html=True)
    with mc2:
        st.markdown(f'<div class="metric-card expense"><h3>💸 Expenses</h3><h2>₹ {te:,.2f}</h2></div>', unsafe_allow_html=True)
    with mc3:
        st.markdown(f'<div class="metric-card balance"><h3>💎 Balance</h3><h2>₹ {net:,.2f}</h2></div>', unsafe_allow_html=True)
    
    rt1, rt2, rt3 = st.tabs(["💰 Income", "💸 Expenses", "📈 Charts"])
    with rt1:
        if bills:
            df_i = pd.DataFrame([{"Bill No": b.get('bill_no',''), "Date": b.get('bill_date',''),
                                  "Pooja": b.get('pooja_type',''), "Type": b.get('devotee_type',''),
                                  "Amount": float(b.get('amount',0))} for b in bills])
            st.dataframe(df_i, use_container_width=True, hide_index=True)
            summary = df_i.groupby('Pooja')['Amount'].agg(['sum','count']).reset_index()
            summary.columns = ['Pooja', 'Total (₹)', 'Count']
            st.dataframe(summary, use_container_width=True, hide_index=True)
            st.download_button("📥 CSV", df_i.to_csv(index=False), "income.csv")
        else:
            st.info("No data")
    with rt2:
        if expenses:
            df_e = pd.DataFrame([{"Date": e.get('expense_date',''), "Type": e.get('expense_type',''),
                                  "Amount": float(e.get('amount',0)), "Desc": e.get('description','')} for e in expenses])
            st.dataframe(df_e, use_container_width=True, hide_index=True)
            st.download_button("📥 CSV", df_e.to_csv(index=False), "expenses.csv")
        else:
            st.info("No data")
    with rt3:
        if bills or expenses:
            st.bar_chart(pd.DataFrame({"Category": ["Income","Expenses"], "Amount": [ti,te]}).set_index("Category"))
            if bills:
                daily = {}
                for b in bills:
                    d = b.get('bill_date','')
                    daily[d] = daily.get(d,0) + float(b.get('amount',0))
                if daily:
                    st.line_chart(pd.DataFrame(sorted(daily.items()), columns=["Date","Income"]).set_index("Date"))


# ============================================================
# PAGE: ASSET MANAGEMENT
# ============================================================
def page_asset_management():
    st.markdown("""
    <div class="main-header">
        <h1>🏷️ Asset Management</h1>
        <p>Track and manage temple assets & donations</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["➕ Add Asset", "📋 Asset List"])
    
    with tab1:
        st.markdown("### ➕ Register New Asset")
        with st.form("asset_form", clear_on_submit=True):
            ac1, ac2 = st.columns(2)
            with ac1:
                asset_tag = st.text_input("🏷️ Asset Tag *", placeholder="e.g. AST-001")
                asset_name = st.text_input("📦 Asset Name *", placeholder="e.g. Bronze Lamp")
                serial_no = st.text_input("🔢 Serial Number", placeholder="e.g. SN-12345")
            with ac2:
                donor_name = st.text_input("🙏 Donor's Name", placeholder="Name of the donor")
                donation_date = st.date_input("📅 Date of Donation", value=date.today(),
                                              min_value=MIN_DATE, max_value=MAX_DATE)
                asset_image = st.file_uploader("📷 Upload Asset Image", type=['jpg', 'jpeg', 'png'])
            
            asset_desc = st.text_area("📝 Description / Notes", height=80, placeholder="Additional details about the asset")
            
            if st.form_submit_button("✅ Register Asset", use_container_width=True):
                if not asset_tag.strip() or not asset_name.strip():
                    st.error("❌ Asset Tag and Asset Name are required!")
                else:
                    image_url = file_to_base64(asset_image)
                    result = db_insert("assets", {
                        "asset_tag": asset_tag.strip(),
                        "asset_name": asset_name.strip(),
                        "serial_no": serial_no,
                        "donor_name": donor_name,
                        "donation_date": str(donation_date),
                        "image_url": image_url,
                        "description": asset_desc
                    })
                    if result:
                        st.success(f"✅ Asset '{asset_name}' registered successfully!")
                        st.rerun()
    
    with tab2:
        st.markdown("### 📋 All Assets")
        
        search_asset = st.text_input("🔍 Search Assets", placeholder="Search by tag, name, or donor")
        
        assets = db_select("assets")
        
        if search_asset:
            assets = [a for a in assets if 
                      search_asset.lower() in a.get('asset_tag', '').lower() or
                      search_asset.lower() in a.get('asset_name', '').lower() or
                      search_asset.lower() in a.get('donor_name', '').lower()]
        
        if assets:
            st.markdown(f"**Total Assets: {len(assets)}**")
            
            for a in assets:
                with st.expander(f"🏷️ {a.get('asset_tag','')} | 📦 {a.get('asset_name','')} | 🙏 {a.get('donor_name','N/A')}"):
                    asc1, asc2 = st.columns([3, 1])
                    with asc1:
                        st.write(f"**Asset Tag:** {a.get('asset_tag', 'N/A')}")
                        st.write(f"**Asset Name:** {a.get('asset_name', 'N/A')}")
                        st.write(f"**Serial No:** {a.get('serial_no', 'N/A')}")
                        st.write(f"**Donor's Name:** {a.get('donor_name', 'N/A')}")
                        st.write(f"**Donation Date:** {a.get('donation_date', 'N/A')}")
                        st.write(f"**Description:** {a.get('description', 'N/A')}")
                    with asc2:
                        if a.get('image_url') and a['image_url'].startswith('data:'):
                            st.markdown(f'<img src="{a["image_url"]}" width="140" style="border-radius:10px; border:2px solid #ff6b35;">', unsafe_allow_html=True)
                    
                    # Edit and Delete
                    btn1, btn2 = st.columns(2)
                    with btn1:
                        if st.button("✏️ Edit", key=f"edit_asset_{a['id']}"):
                            st.session_state[f"editing_asset_{a['id']}"] = not st.session_state.get(f"editing_asset_{a['id']}", False)
                            st.rerun()
                    with btn2:
                        if st.button("🗑️ Delete", key=f"del_asset_{a['id']}"):
                            db_delete("assets", "id", a['id'])
                            st.success("✅ Asset deleted!")
                            st.rerun()
                    
                    if st.session_state.get(f"editing_asset_{a['id']}", False):
                        with st.form(f"edit_asset_form_{a['id']}"):
                            st.markdown("### ✏️ Edit Asset")
                            eac1, eac2 = st.columns(2)
                            with eac1:
                                ea_tag = st.text_input("Tag", value=a.get('asset_tag',''), key=f"eat_{a['id']}")
                                ea_name = st.text_input("Name", value=a.get('asset_name',''), key=f"ean_{a['id']}")
                                ea_sn = st.text_input("Serial No", value=a.get('serial_no',''), key=f"eas_{a['id']}")
                            with eac2:
                                ea_donor = st.text_input("Donor", value=a.get('donor_name',''), key=f"ead_{a['id']}")
                                ea_date_val = date.today()
                                if a.get('donation_date'):
                                    try:
                                        ea_date_val = datetime.strptime(str(a['donation_date']), '%Y-%m-%d').date()
                                    except:
                                        pass
                                ea_date = st.date_input("Date", value=ea_date_val, key=f"eadd_{a['id']}",
                                                        min_value=MIN_DATE, max_value=MAX_DATE)
                            ea_desc = st.text_area("Description", value=a.get('description',''), key=f"eadesc_{a['id']}")
                            ea_img = st.file_uploader("New Image", type=['jpg','jpeg','png'], key=f"eaimg_{a['id']}")
                            
                            if st.form_submit_button("💾 Save"):
                                update_data = {
                                    "asset_tag": ea_tag, "asset_name": ea_name,
                                    "serial_no": ea_sn, "donor_name": ea_donor,
                                    "donation_date": str(ea_date), "description": ea_desc
                                }
                                if ea_img:
                                    update_data["image_url"] = file_to_base64(ea_img)
                                db_update("assets", update_data, "id", a['id'])
                                st.session_state[f"editing_asset_{a['id']}"] = False
                                st.success("✅ Updated!")
                                st.rerun()
        else:
            st.info("No assets registered yet. Add your first asset!")


# ============================================================
# PAGE: SETTINGS
# ============================================================
def page_settings():
    st.markdown("""
    <div class="main-header">
        <h1>⚙️ Settings</h1>
        <p>Configure pooja types, expense types & news</p>
    </div>
    """, unsafe_allow_html=True)
    
    t1, t2, t3 = st.tabs(["🙏 Pooja Types", "💸 Expense Types", "📢 News Ticker"])
    
    with t1:
        pts = db_select("pooja_types")
        for p in pts:
            pc1, pc2 = st.columns([5, 1])
            with pc1:
                st.write(f"🙏 **{p['name']}** — ₹{p.get('amount',0)}")
            with pc2:
                if st.button("🗑️", key=f"dpt_{p['id']}"):
                    db_delete("pooja_types", "id", p['id']); st.rerun()
        with st.form("add_pt", clear_on_submit=True):
            apc1, apc2 = st.columns(2)
            with apc1:
                new_pt = st.text_input("Name")
            with apc2:
                new_pt_amt = st.number_input("Amount", min_value=0.0, step=10.0)
            if st.form_submit_button("➕ Add"):
                if new_pt.strip():
                    db_insert("pooja_types", {"name": new_pt.strip(), "amount": new_pt_amt})
                    st.success("✅ Added!"); st.rerun()
    
    with t2:
        ets = db_select("expense_types")
        for e in ets:
            ec1, ec2 = st.columns([5, 1])
            with ec1:
                st.write(f"💸 **{e['name']}**")
            with ec2:
                if st.button("🗑️", key=f"det_{e['id']}"):
                    db_delete("expense_types", "id", e['id']); st.rerun()
        with st.form("add_et", clear_on_submit=True):
            new_et = st.text_input("Name")
            if st.form_submit_button("➕ Add"):
                if new_et.strip():
                    db_insert("expense_types", {"name": new_et.strip()})
                    st.success("✅ Added!"); st.rerun()
    
    with t3:
        news = db_select("news_ticker")
        for n in news:
            nc1, nc2, nc3 = st.columns([4, 1, 1])
            with nc1:
                st.write(f"{'🟢' if n.get('is_active') else '🔴'} {n['message']}")
            with nc2:
                if st.button("Toggle", key=f"tn_{n['id']}"):
                    db_update("news_ticker", {"is_active": not n.get('is_active', True)}, "id", n['id']); st.rerun()
            with nc3:
                if st.button("🗑️", key=f"dn_{n['id']}"):
                    db_delete("news_ticker", "id", n['id']); st.rerun()
        with st.form("add_news", clear_on_submit=True):
            new_msg = st.text_input("Message")
            if st.form_submit_button("➕ Add"):
                if new_msg.strip():
                    db_insert("news_ticker", {"message": new_msg.strip(), "is_active": True})
                    st.success("✅ Added!"); st.rerun()


# ============================================================
# PAGE: USER MANAGEMENT
# ============================================================
def page_users():
    st.markdown("""
    <div class="main-header">
        <h1>👥 User Management</h1>
        <p>Create and manage users</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.user_role != 'admin':
        st.error("❌ Admin only!"); return
    
    t1, t2 = st.tabs(["➕ Create", "📋 Manage"])
    with t1:
        with st.form("cu", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                nu = st.text_input("Username")
                np = st.text_input("Password", type="password")
            with c2:
                cp = st.text_input("Confirm", type="password")
                nr = st.selectbox("Role", ["user", "admin"])
            if st.form_submit_button("➕ Create", use_container_width=True):
                if not nu or not np:
                    st.error("Fill all!")
                elif np != cp:
                    st.error("Mismatch!")
                elif db_select("users", filters={"username": nu}):
                    st.error("Exists!")
                else:
                    db_insert("users", {"username": nu, "password_hash": np, "role": nr})
                    st.success(f"✅ '{nu}' created!"); st.rerun()
    with t2:
        for u in db_select("users"):
            uc1, uc2 = st.columns([5, 1])
            with uc1:
                st.write(f"{'👑' if u.get('role')=='admin' else '👤'} **{u['username']}** ({u.get('role','user')})")
            with uc2:
                if u['username'] != 'admin':
                    if st.button("🗑️", key=f"du_{u['id']}"):
                        db_delete("users", "id", u['id']); st.rerun()


# ============================================================
# PAGE: SAMAYA VAKUPPU
# ============================================================
def page_samaya_vakuppu():
    st.markdown("""
    <div class="main-header">
        <h1>📚 Samaya Vakuppu</h1>
        <p>Religious education student management</p>
    </div>
    """, unsafe_allow_html=True)
    
    t1, t2 = st.tabs(["➕ Add", "📋 List"])
    with t1:
        with st.form("sv", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                sn = st.text_input("👤 Student Name *")
                sd = st.date_input("📅 DOB", value=date(2010,1,1), min_value=MIN_DATE, max_value=MAX_DATE)
                sa = st.text_area("🏠 Address", height=80)
                spt = st.selectbox("👪 Parent", ["Father", "Mother"])
                spn = st.text_input("👤 Parent Name")
            with c2:
                sbd = st.date_input("📅 Bond Date", min_value=MIN_DATE, max_value=MAX_DATE)
                sbk = st.text_input("🏦 Bank")
                sbr = st.text_input("🏦 Branch")
                sbn = st.text_input("📋 Bond No")
                sbf = st.file_uploader("📄 Bond Scan", type=['jpg','jpeg','png','pdf'], key="svb")
                sph = st.file_uploader("📷 Photo", type=['jpg','jpeg','png'], key="svp")
            if st.form_submit_button("✅ Register", use_container_width=True):
                if sn.strip():
                    db_insert("samaya_vakuppu", {
                        "student_name": sn.strip(), "dob": str(sd), "address": sa,
                        "parent_name": spn, "parent_type": spt, "bond_issue_date": str(sbd),
                        "scanned_bond_url": file_to_base64(sbf), "photo_url": file_to_base64(sph),
                        "bond_issuing_bank": sbk, "branch_of_bank": sbr, "bond_no": sbn
                    })
                    st.success(f"✅ '{sn}' registered!"); st.rerun()
    with t2:
        students = db_select("samaya_vakuppu")
        ss = st.text_input("🔍 Search", key="ssv")
        if ss:
            students = [s for s in students if ss.lower() in s.get('student_name','').lower()]
        for s in students:
            with st.expander(f"👤 {s['student_name']} | Bond: {s.get('bond_no','N/A')}"):
                sc1, sc2 = st.columns([3, 1])
                with sc1:
                    for l, k in [("Name","student_name"),("DOB","dob"),("Address","address"),
                                 ("Parent","parent_name"),("Type","parent_type"),("Bond Date","bond_issue_date"),
                                 ("Bank","bond_issuing_bank"),("Branch","branch_of_bank"),("Bond No","bond_no")]:
                        st.write(f"**{l}:** {s.get(k,'N/A')}")
                with sc2:
                    if s.get('photo_url') and s['photo_url'].startswith('data:'):
                        st.markdown(f'<img src="{s["photo_url"]}" width="120" style="border-radius:10px;">', unsafe_allow_html=True)
                if st.button("🗑️ Delete", key=f"dsv_{s['id']}"):
                    db_delete("samaya_vakuppu", "id", s['id']); st.rerun()


# ============================================================
# PAGE: THIRUMANA MANDAPAM
# ============================================================
def page_thirumana_mandapam():
    st.markdown("""
    <div class="main-header">
        <h1>💒 Thirumana Mandapam</h1>
        <p>Marriage hall bond management</p>
    </div>
    """, unsafe_allow_html=True)
    
    t1, t2 = st.tabs(["➕ Add", "📋 Records"])
    with t1:
        with st.form("tm", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                tn = st.text_input("👤 Name *")
                ta = st.text_area("🏠 Address", height=80)
                tb = st.text_input("📋 Bond No")
                td = st.date_input("📅 Bond Date", min_value=MIN_DATE, max_value=MAX_DATE)
            with c2:
                tam = st.number_input("💰 Amount", min_value=0.0, step=100.0)
                tnb = st.number_input("📋 No. of Bonds", min_value=0, step=1)
                ts = st.file_uploader("📄 Scan", type=['jpg','jpeg','png','pdf'], key="tms")
                tp = st.file_uploader("📷 Photo", type=['jpg','jpeg','png'], key="tmp")
            if st.form_submit_button("✅ Save", use_container_width=True):
                if tn.strip():
                    db_insert("thirumana_mandapam", {
                        "name": tn.strip(), "address": ta, "bond_no": tb,
                        "bond_issued_date": str(td), "amount": tam, "no_of_bonds": tnb,
                        "scan_copy_url": file_to_base64(ts), "photo_url": file_to_base64(tp)
                    })
                    st.success(f"✅ '{tn}' saved!"); st.rerun()
    with t2:
        records = db_select("thirumana_mandapam")
        stm = st.text_input("🔍 Search", key="stm")
        if stm:
            records = [r for r in records if stm.lower() in r.get('name','').lower()]
        for r in records:
            with st.expander(f"👤 {r['name']} | Bond: {r.get('bond_no','N/A')} | ₹{r.get('amount',0)}"):
                rc1, rc2 = st.columns([3, 1])
                with rc1:
                    for l, k in [("Name","name"),("Address","address"),("Bond No","bond_no"),
                                 ("Date","bond_issued_date"),("Amount","amount"),("Bonds","no_of_bonds")]:
                        v = r.get(k,'N/A')
                        if k == 'amount' and v != 'N/A':
                            v = f"₹ {float(v):,.2f}"
                        st.write(f"**{l}:** {v}")
                with rc2:
                    if r.get('photo_url') and r['photo_url'].startswith('data:'):
                        st.markdown(f'<img src="{r["photo_url"]}" width="120" style="border-radius:10px;">', unsafe_allow_html=True)
                if st.button("🗑️ Delete", key=f"dtm_{r['id']}"):
                    db_delete("thirumana_mandapam", "id", r['id']); st.rerun()


# ============================================================
# SIDEBAR
# ============================================================
def render_sidebar():
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align:center; padding:15px; background:linear-gradient(135deg,#ff6b35,#f7c948);
                    border-radius:10px; margin-bottom:15px;">
            <h2 style="color:#8B0000; margin:0;">🛕</h2>
            <p style="color:#5a1a00; margin:3px 0 0 0; font-weight:600; font-size:0.75em;">
                Sree Bhadreshwari Amman<br>Temple Management System
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="color:#ccc; padding:5px 10px; font-size:0.85em;">
            👤 <strong style="color:#f7c948;">{st.session_state.username}</strong>
            <span style="color:#888;">({st.session_state.user_role})</span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        
        pages = [
            ("🏠 Dashboard", "Dashboard"),
            ("👥 Devotee Enrollment", "Devotee Enrollment"),
            ("🧾 Billing", "Billing"),
            ("💸 Expenses", "Expenses"),
            ("📊 Reports", "Reports"),
            ("🏷️ Asset Management", "Asset Management"),
            ("📚 Samaya Vakuppu", "Samaya Vakuppu"),
            ("💒 Thirumana Mandapam", "Thirumana Mandapam"),
            ("⚙️ Settings", "Settings"),
            ("👥 User Management", "User Management"),
        ]
        
        for label, page_name in pages:
            if page_name == "User Management" and st.session_state.user_role != 'admin':
                continue
            if st.button(label, key=f"nav_{page_name}", use_container_width=True):
                st.session_state.current_page = page_name
                st.rerun()
        
        st.markdown("---")
        if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
            for key in ['logged_in', 'username', 'user_role', 'current_page']:
                st.session_state[key] = defaults[key]
            st.rerun()
        
        st.markdown("""
        <div style="text-align:center; padding:20px 0 10px 0; color:#555; font-size:0.7em;">
            Sree Bhadreshwari Amman Temple<br>Management System v1.0<br>
            🙏 அம்மே நாராயணா 🙏
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# MAIN ROUTER
# ============================================================
def main():
    if not st.session_state.logged_in:
        page_login()
    else:
        render_sidebar()
        page_map = {
            "Dashboard": page_dashboard,
            "Devotee Enrollment": page_devotee_enrollment,
            "Billing": page_billing,
            "Expenses": page_expenses,
            "Reports": page_reports,
            "Asset Management": page_asset_management,
            "Samaya Vakuppu": page_samaya_vakuppu,
            "Thirumana Mandapam": page_thirumana_mandapam,
            "Settings": page_settings,
            "User Management": page_users,
        }
        current = st.session_state.current_page
        if current in page_map:
            page_map[current]()
        else:
            page_dashboard()

if __name__ == "__main__":
    main()
