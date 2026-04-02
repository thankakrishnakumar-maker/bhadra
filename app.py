# app.py
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from supabase import create_client, Client
import uuid
import base64
import hashlib
import json
import time

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="🛕 Temple Management System",
    page_icon="🛕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# SUPABASE CONNECTION
# ============================================================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = get_supabase_client()

# ============================================================
# NATCHATHIRAM LIST
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
    "பூரட்டாதி (Purva Bhadrapada)", "உத்திரட்டாதி (Uttara Bhadrapada)", "ரேவதி (Revati)"
]

RELATION_TYPES = ["Self", "Spouse", "Son", "Daughter", "Father", "Mother", 
                  "Brother", "Sister", "Grandfather", "Grandmother", "Other"]

# ============================================================
# CUSTOM CSS
# ============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    
    * { font-family: 'Poppins', sans-serif; }
    
    .main-header {
        background: linear-gradient(135deg, #ff6b35 0%, #f7c948 50%, #ff6b35 100%);
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(255, 107, 53, 0.3);
    }
    .main-header h1 {
        color: #8B0000;
        font-size: 2.2em;
        margin: 0;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    .main-header p {
        color: #5a1a00;
        font-size: 1em;
        margin: 5px 0 0 0;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin: 5px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
    }
    .metric-card.income {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    }
    .metric-card.expense {
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
    }
    .metric-card.balance {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    .metric-card h3 { margin: 0; font-size: 0.9em; opacity: 0.9; }
    .metric-card h2 { margin: 5px 0 0 0; font-size: 1.8em; }
    
    .news-ticker {
        background: linear-gradient(90deg, #1a1a2e, #16213e, #0f3460);
        color: #f7c948;
        padding: 12px 20px;
        border-radius: 10px;
        overflow: hidden;
        white-space: nowrap;
        font-size: 1em;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    .news-ticker .ticker-content {
        display: inline-block;
        animation: ticker 30s linear infinite;
    }
    @keyframes ticker {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }
    
    .pooja-card {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 15px;
        border-radius: 10px;
        margin: 5px 0;
        border-left: 4px solid #ff6b35;
    }
    
    .birthday-card {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 10px 15px;
        border-radius: 10px;
        margin: 5px 0;
        border-left: 4px solid #e91e63;
    }
    
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    
    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        padding: 15px;
        border-radius: 10px;
        color: #155724;
        margin: 10px 0;
    }
    
    .warning-box {
        background: #fff3cd;
        border: 1px solid #ffeeba;
        padding: 15px;
        border-radius: 10px;
        color: #856404;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'user_role' not in st.session_state:
    st.session_state.user_role = ""
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def safe_query(table, select="*", filters=None):
    """Safe database query with error handling"""
    try:
        query = supabase.table(table).select(select)
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        result = query.execute()
        return result.data if result.data else []
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return []

def safe_insert(table, data):
    """Safe database insert"""
    try:
        result = supabase.table(table).insert(data).execute()
        return result.data
    except Exception as e:
        st.error(f"Insert error: {str(e)}")
        return None

def safe_update(table, data, match_field, match_value):
    """Safe database update"""
    try:
        result = supabase.table(table).update(data).eq(match_field, match_value).execute()
        return result.data
    except Exception as e:
        st.error(f"Update error: {str(e)}")
        return None

def safe_delete(table, match_field, match_value):
    """Safe database delete"""
    try:
        result = supabase.table(table).delete().eq(match_field, match_value).execute()
        return result.data
    except Exception as e:
        st.error(f"Delete error: {str(e)}")
        return None

def upload_to_supabase_storage(file, bucket, path):
    """Upload file and return public URL - stores as base64 in description field"""
    try:
        file_bytes = file.read()
        encoded = base64.b64encode(file_bytes).decode()
        return f"data:{file.type};base64,{encoded}"
    except Exception as e:
        st.error(f"Upload error: {str(e)}")
        return None

def get_today_birthdays():
    """Get today's birthdays from devotees and family members"""
    today = date.today()
    birthdays = []
    
    devotees = safe_query("devotees")
    for d in devotees:
        if d.get('dob'):
            try:
                dob = datetime.strptime(d['dob'], '%Y-%m-%d').date()
                if dob.month == today.month and dob.day == today.day:
                    birthdays.append({"name": d['name'], "type": "Devotee"})
            except:
                pass
    
    members = safe_query("family_members")
    for m in members:
        if m.get('dob'):
            try:
                dob = datetime.strptime(m['dob'], '%Y-%m-%d').date()
                if dob.month == today.month and dob.day == today.day:
                    birthdays.append({"name": m['name'], "type": "Family Member"})
            except:
                pass
    
    return birthdays

def get_income_for_period(start_date, end_date):
    """Get total income for a date range"""
    try:
        result = supabase.table("bills").select("amount, bill_date").gte("bill_date", str(start_date)).lte("bill_date", str(end_date)).execute()
        if result.data:
            return sum(float(b.get('amount', 0)) for b in result.data)
        return 0
    except:
        return 0

def get_expenses_for_period(start_date, end_date):
    """Get total expenses for a date range"""
    try:
        result = supabase.table("expenses").select("amount, expense_date").gte("expense_date", str(start_date)).lte("expense_date", str(end_date)).execute()
        if result.data:
            return sum(float(e.get('amount', 0)) for e in result.data)
        return 0
    except:
        return 0

def generate_bill_no():
    """Generate unique bill number"""
    return f"BILL-{datetime.now().strftime('%Y%m%d%H%M%S')}"

# ============================================================
# LOGIN PAGE
# ============================================================
def login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="main-header">
            <h1>🛕 Temple Management System</h1>
            <p>🙏 ஓம் நமசிவாய 🙏</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🔐 Login")
        
        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="Enter username")
            password = st.text_input("🔑 Password", type="password", placeholder="Enter password")
            submitted = st.form_submit_button("🚀 Login", use_container_width=True)
            
            if submitted:
                if username and password:
                    users = safe_query("users", filters={"username": username})
                    if users and users[0].get('password_hash') == password:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.user_role = users[0].get('role', 'user')
                        st.success("✅ Login successful!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password!")
                else:
                    st.warning("⚠️ Please enter both username and password!")

# ============================================================
# DASHBOARD PAGE
# ============================================================
def dashboard_page():
    st.markdown("""
    <div class="main-header">
        <h1>🛕 Temple Management Dashboard</h1>
        <p>🙏 ஓம் நமசிவாய - Welcome to Temple Management System 🙏</p>
    </div>
    """, unsafe_allow_html=True)
    
    # --- News Ticker with Birthday Wishes ---
    birthdays = get_today_birthdays()
    news_items = safe_query("news_ticker", filters={"is_active": True})
    
    ticker_parts = []
    if birthdays:
        bday_names = " 🎂 ".join([f"🎉 Happy Birthday {b['name']}!" for b in birthdays])
        ticker_parts.append(bday_names)
    if news_items:
        news_text = " 📢 ".join([n['message'] for n in news_items])
        ticker_parts.append(news_text)
    if not ticker_parts:
        ticker_parts.append("🛕 Welcome to Temple Management System 🙏 May God Bless You! 🙏")
    
    ticker_text = " &nbsp;&nbsp;&nbsp; ⭐ &nbsp;&nbsp;&nbsp; ".join(ticker_parts)
    
    st.markdown(f"""
    <div class="news-ticker">
        <div class="ticker-content">
            {ticker_text}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # --- Period Selection ---
    st.markdown("---")
    period = st.selectbox("📅 Select Period", ["Daily", "Weekly", "Monthly", "Yearly"], index=0)
    
    today = date.today()
    if period == "Daily":
        start_date = today
        end_date = today
    elif period == "Weekly":
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif period == "Monthly":
        start_date = today.replace(day=1)
        end_date = today
    else:  # Yearly
        start_date = today.replace(month=1, day=1)
        end_date = today
    
    income = get_income_for_period(start_date, end_date)
    expenses = get_expenses_for_period(start_date, end_date)
    balance = income - expenses
    
    # --- Metric Cards ---
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card income">
            <h3>💰 {period} Income</h3>
            <h2>₹ {income:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card expense">
            <h3>💸 {period} Expenses</h3>
            <h2>₹ {expenses:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card balance">
            <h3>💎 {period} Balance</h3>
            <h2>₹ {balance:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        total_devotees = len(safe_query("devotees"))
        st.markdown(f"""
        <div class="metric-card">
            <h3>👥 Total Devotees</h3>
            <h2>{total_devotees}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # --- Two Column Layout ---
    col_left, col_right = st.columns(2)
    
    with col_left:
        # Today's Birthdays
        st.markdown("### 🎂 Today's Birthdays")
        if birthdays:
            for b in birthdays:
                st.markdown(f"""
                <div class="birthday-card">
                    🎉 <strong>{b['name']}</strong> ({b['type']}) - Happy Birthday! 🎂🎈
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No birthdays today")
    
    with col_right:
        # Daily Pooja
        st.markdown("### 🙏 Daily Pooja Schedule")
        daily_poojas = safe_query("daily_pooja", filters={"pooja_date": str(today)})
        if daily_poojas:
            for p in daily_poojas:
                status_icon = "✅" if p.get('status') == 'completed' else "⏳"
                st.markdown(f"""
                <div class="pooja-card">
                    {status_icon} <strong>{p['pooja_name']}</strong> - {p.get('pooja_time', 'N/A')}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No pooja scheduled for today")
        
        # Add Daily Pooja
        with st.expander("➕ Add Daily Pooja"):
            with st.form("add_daily_pooja"):
                dp_name = st.text_input("Pooja Name")
                dp_time = st.text_input("Pooja Time (e.g., 6:00 AM)")
                dp_date = st.date_input("Pooja Date", value=today)
                if st.form_submit_button("Add Pooja"):
                    if dp_name:
                        safe_insert("daily_pooja", {
                            "pooja_name": dp_name,
                            "pooja_time": dp_time,
                            "pooja_date": str(dp_date),
                            "status": "pending"
                        })
                        st.success("✅ Daily pooja added!")
                        st.rerun()
    
    # --- Income vs Expenses Chart ---
    st.markdown("---")
    st.markdown("### 📊 Income vs Expenses Overview")
    
    chart_data = {
        "Category": ["Income", "Expenses", "Balance"],
        "Amount": [income, expenses, balance]
    }
    df_chart = pd.DataFrame(chart_data)
    st.bar_chart(df_chart.set_index("Category"))

# ============================================================
# DEVOTEE ENROLLMENT PAGE
# ============================================================
def devotee_enrollment_page():
    st.markdown("""
    <div class="main-header">
        <h1>👥 Devotee Enrollment</h1>
        <p>Register devotees and family members</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["➕ New Enrollment", "🔍 Search & Manage", "👨‍👩‍👧‍👦 Family Members"])
    
    # --- TAB 1: New Enrollment ---
    with tab1:
        st.markdown("### 👤 Family Head Registration")
        
        with st.form("devotee_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("👤 Full Name *", placeholder="Enter full name")
                dob = st.date_input("📅 Date of Birth", value=date(1990, 1, 1), min_value=date(1900, 1, 1))
                relation_type = st.selectbox("👪 Relation Type", RELATION_TYPES)
                mobile_no = st.text_input("📱 Mobile Number", placeholder="Enter mobile number")
                whatsapp_no = st.text_input("📲 WhatsApp Number", placeholder="Enter WhatsApp number")
            
            with col2:
                wedding_day = st.date_input("💒 Wedding Day", value=None)
                natchathiram = st.selectbox("⭐ Natchathiram (Star)", ["Select"] + NATCHATHIRAM_LIST)
                address = st.text_area("🏠 Address", placeholder="Enter full address")
                photo = st.file_uploader("📷 Photo", type=['jpg', 'jpeg', 'png'])
            
            # Yearly Pooja Section
            st.markdown("### 🙏 Yearly Pooja Details")
            st.markdown("*You can add more yearly poojas after enrollment from the manage section*")
            
            yp_col1, yp_col2, yp_col3 = st.columns(3)
            with yp_col1:
                pooja_types = safe_query("pooja_types")
                pooja_names = [p['name'] for p in pooja_types] if pooja_types else []
                yearly_pooja_type = st.selectbox("Pooja Type", ["Select"] + pooja_names, key="yp_type1")
            with yp_col2:
                yearly_pooja_date = st.date_input("Pooja Date", key="yp_date1")
            with yp_col3:
                yearly_pooja_desc = st.text_input("Description", key="yp_desc1")
            
            submitted = st.form_submit_button("✅ Register Devotee", use_container_width=True)
            
            if submitted:
                if not name:
                    st.error("❌ Name is required!")
                else:
                    photo_url = None
                    if photo:
                        photo_url = upload_to_supabase_storage(photo, "photos", f"devotees/{name}")
                    
                    devotee_data = {
                        "name": name,
                        "dob": str(dob),
                        "relation_type": relation_type,
                        "mobile_no": mobile_no,
                        "whatsapp_no": whatsapp_no,
                        "wedding_day": str(wedding_day) if wedding_day else None,
                        "natchathiram": natchathiram if natchathiram != "Select" else None,
                        "address": address,
                        "photo_url": photo_url
                    }
                    
                    result = safe_insert("devotees", devotee_data)
                    
                    if result:
                        # Add yearly pooja if provided
                        if yearly_pooja_type != "Select":
                            safe_insert("devotee_yearly_pooja", {
                                "devotee_id": result[0]['id'],
                                "pooja_type": yearly_pooja_type,
                                "pooja_date": str(yearly_pooja_date),
                                "description": yearly_pooja_desc
                            })
                        
                        st.success(f"✅ Devotee '{name}' registered successfully!")
                        st.rerun()
    
    # --- TAB 2: Search & Manage ---
    with tab2:
        st.markdown("### 🔍 Search Devotees")
        
        search_col1, search_col2, search_col3 = st.columns(3)
        with search_col1:
            search_name = st.text_input("Search by Name", placeholder="Enter name")
        with search_col2:
            search_mobile = st.text_input("Search by Mobile", placeholder="Enter mobile")
        with search_col3:
            search_address = st.text_input("Search by Address", placeholder="Enter address")
        
        devotees = safe_query("devotees")
        
        # Apply filters
        if search_name:
            devotees = [d for d in devotees if search_name.lower() in d.get('name', '').lower()]
        if search_mobile:
            devotees = [d for d in devotees if search_mobile in d.get('mobile_no', '')]
        if search_address:
            devotees = [d for d in devotees if search_address.lower() in d.get('address', '').lower()]
        
        if devotees:
            for devotee in devotees:
                with st.expander(f"👤 {devotee['name']} | 📱 {devotee.get('mobile_no', 'N/A')} | ⭐ {devotee.get('natchathiram', 'N/A')}"):
                    det_col1, det_col2 = st.columns([3, 1])
                    
                    with det_col1:
                        st.write(f"**Name:** {devotee['name']}")
                        st.write(f"**DOB:** {devotee.get('dob', 'N/A')}")
                        st.write(f"**Mobile:** {devotee.get('mobile_no', 'N/A')}")
                        st.write(f"**WhatsApp:** {devotee.get('whatsapp_no', 'N/A')}")
                        st.write(f"**Relation:** {devotee.get('relation_type', 'N/A')}")
                        st.write(f"**Wedding Day:** {devotee.get('wedding_day', 'N/A')}")
                        st.write(f"**Natchathiram:** {devotee.get('natchathiram', 'N/A')}")
                        st.write(f"**Address:** {devotee.get('address', 'N/A')}")
                    
                    with det_col2:
                        if devotee.get('photo_url') and devotee['photo_url'].startswith('data:'):
                            st.markdown(f'<img src="{devotee["photo_url"]}" width="150" style="border-radius:10px;">', unsafe_allow_html=True)
                    
                    # Yearly Poojas
                    st.markdown("**🙏 Yearly Poojas:**")
                    yearly_poojas = safe_query("devotee_yearly_pooja", filters={"devotee_id": devotee['id']})
                    if yearly_poojas:
                        for yp in yearly_poojas:
                            st.write(f"  - {yp['pooja_type']} on {yp.get('pooja_date', 'N/A')} - {yp.get('description', '')}")
                    
                    # Add more yearly poojas
                    with st.form(f"add_yp_{devotee['id']}"):
                        st.markdown("**➕ Add Yearly Pooja:**")
                        ayp_col1, ayp_col2, ayp_col3 = st.columns(3)
                        with ayp_col1:
                            pooja_types_list = safe_query("pooja_types")
                            pt_names = [p['name'] for p in pooja_types_list] if pooja_types_list else []
                            new_yp_type = st.selectbox("Pooja Type", ["Select"] + pt_names, key=f"nyp_t_{devotee['id']}")
                        with ayp_col2:
                            new_yp_date = st.date_input("Date", key=f"nyp_d_{devotee['id']}")
                        with ayp_col3:
                            new_yp_desc = st.text_input("Description", key=f"nyp_desc_{devotee['id']}")
                        
                        if st.form_submit_button("Add Yearly Pooja"):
                            if new_yp_type != "Select":
                                safe_insert("devotee_yearly_pooja", {
                                    "devotee_id": devotee['id'],
                                    "pooja_type": new_yp_type,
                                    "pooja_date": str(new_yp_date),
                                    "description": new_yp_desc
                                })
                                st.success("✅ Yearly pooja added!")
                                st.rerun()
                    
                    # Edit & Delete buttons
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button(f"✏️ Edit", key=f"edit_{devotee['id']}"):
                            st.session_state[f"editing_{devotee['id']}"] = True
                            st.rerun()
                    with btn_col2:
                        if st.button(f"🗑️ Delete", key=f"del_{devotee['id']}"):
                            safe_delete("devotee_yearly_pooja", "devotee_id", devotee['id'])
                            safe_delete("family_members", "devotee_id", devotee['id'])
                            safe_delete("devotees", "id", devotee['id'])
                            st.success(f"✅ Devotee '{devotee['name']}' deleted!")
                            st.rerun()
                    
                    # Edit Form
                    if st.session_state.get(f"editing_{devotee['id']}", False):
                        with st.form(f"edit_form_{devotee['id']}"):
                            st.markdown("### ✏️ Edit Devotee")
                            ec1, ec2 = st.columns(2)
                            with ec1:
                                e_name = st.text_input("Name", value=devotee.get('name', ''))
                                e_dob = st.date_input("DOB", value=datetime.strptime(devotee['dob'], '%Y-%m-%d').date() if devotee.get('dob') else date(1990,1,1))
                                e_mobile = st.text_input("Mobile", value=devotee.get('mobile_no', ''))
                                e_whatsapp = st.text_input("WhatsApp", value=devotee.get('whatsapp_no', ''))
                            with ec2:
                                e_relation = st.selectbox("Relation", RELATION_TYPES, index=RELATION_TYPES.index(devotee.get('relation_type', 'Self')) if devotee.get('relation_type') in RELATION_TYPES else 0)
                                curr_star = devotee.get('natchathiram', '')
                                star_list = ["Select"] + NATCHATHIRAM_LIST
                                star_idx = star_list.index(curr_star) if curr_star in star_list else 0
                                e_natchathiram = st.selectbox("Natchathiram", star_list, index=star_idx)
                                e_address = st.text_area("Address", value=devotee.get('address', ''))
                            
                            if st.form_submit_button("💾 Save Changes"):
                                safe_update("devotees", {
                                    "name": e_name,
                                    "dob": str(e_dob),
                                    "mobile_no": e_mobile,
                                    "whatsapp_no": e_whatsapp,
                                    "relation_type": e_relation,
                                    "natchathiram": e_natchathiram if e_natchathiram != "Select" else None,
                                    "address": e_address
                                }, "id", devotee['id'])
                                st.session_state[f"editing_{devotee['id']}"] = False
                                st.success("✅ Updated successfully!")
                                st.rerun()
        else:
            st.info("No devotees found. Start by enrolling a new devotee!")
    
    # --- TAB 3: Family Members ---
    with tab3:
        st.markdown("### 👨‍👩‍👧‍👦 Manage Family Members")
        
        devotees_list = safe_query("devotees")
        if devotees_list:
            devotee_options = {f"{d['name']} ({d.get('mobile_no', 'N/A')})": d['id'] for d in devotees_list}
            selected_devotee = st.selectbox("Select Family Head", list(devotee_options.keys()))
            
            if selected_devotee:
                devotee_id = devotee_options[selected_devotee]
                
                # Show existing family members
                family_members = safe_query("family_members", filters={"devotee_id": devotee_id})
                
                if family_members:
                    st.markdown("**Existing Family Members:**")
                    for fm in family_members:
                        fm_col1, fm_col2 = st.columns([4, 1])
                        with fm_col1:
                            st.write(f"👤 **{fm['name']}** | Relation: {fm.get('relation_type', 'N/A')} | DOB: {fm.get('dob', 'N/A')} | Star: {fm.get('natchathiram', 'N/A')}")
                        with fm_col2:
                            if st.button("🗑️", key=f"del_fm_{fm['id']}"):
                                safe_delete("family_members", "id", fm['id'])
                                st.success("Deleted!")
                                st.rerun()
                
                # Add new family member
                st.markdown("---")
                st.markdown("### ➕ Add Family Member")
                
                with st.form("add_family_member", clear_on_submit=True):
                    fm_col1, fm_col2 = st.columns(2)
                    with fm_col1:
                        fm_name = st.text_input("👤 Name *")
                        fm_dob = st.date_input("📅 Date of Birth", value=date(1990, 1, 1))
                        fm_relation = st.selectbox("👪 Relation Type", RELATION_TYPES)
                    with fm_col2:
                        fm_wedding = st.date_input("💒 Wedding Day", value=None, key="fm_wedding")
                        fm_star = st.selectbox("⭐ Natchathiram", ["Select"] + NATCHATHIRAM_LIST, key="fm_star")
                    
                    if st.form_submit_button("➕ Add Family Member", use_container_width=True):
                        if fm_name:
                            safe_insert("family_members", {
                                "devotee_id": devotee_id,
                                "name": fm_name,
                                "dob": str(fm_dob),
                                "relation_type": fm_relation,
                                "wedding_day": str(fm_wedding) if fm_wedding else None,
                                "natchathiram": fm_star if fm_star != "Select" else None
                            })
                            st.success(f"✅ Family member '{fm_name}' added!")
                            st.rerun()
                        else:
                            st.error("❌ Name is required!")
        else:
            st.info("No devotees enrolled yet. Please enroll a family head first.")

# ============================================================
# BILLING PAGE
# ============================================================
def billing_page():
    st.markdown("""
    <div class="main-header">
        <h1>🧾 Billing</h1>
        <p>Generate bills for pooja services</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["➕ New Bill", "📋 Bill History"])
    
    with tab1:
        st.markdown("### 🧾 Create New Bill")
        
        # Devotee Type Selection
        devotee_type = st.radio("Select Devotee Type", ["Enrolled Devotee", "Guest Devotee"], horizontal=True)
        
        bill_col1, bill_col2 = st.columns(2)
        
        with bill_col1:
            manual_bill_no = st.text_input("📝 Manual Bill No", placeholder="Enter manual bill number")
            bill_book_no = st.text_input("📖 Bill Book No", placeholder="Enter bill book number")
            
            # Pooja Type
            pooja_types = safe_query("pooja_types")
            pooja_options = {f"{p['name']} - ₹{p.get('amount', 0)}": p for p in pooja_types} if pooja_types else {}
            selected_pooja = st.selectbox("🙏 Pooja Type", list(pooja_options.keys()) if pooja_options else ["No pooja types configured"])
            
            if selected_pooja and selected_pooja in pooja_options:
                amount = st.number_input("💰 Amount", value=float(pooja_options[selected_pooja].get('amount', 0)), min_value=0.0, step=10.0)
            else:
                amount = st.number_input("💰 Amount", value=0.0, min_value=0.0, step=10.0)
            
            bill_date = st.date_input("📅 Bill Date", value=date.today())
        
        with bill_col2:
            devotee_id = None
            guest_name = ""
            guest_address = ""
            guest_mobile = ""
            guest_whatsapp = ""
            
            if devotee_type == "Enrolled Devotee":
                st.markdown("### 🔍 Search Enrolled Devotee")
                
                search_type = st.selectbox("Search By", ["Name", "Mobile", "WhatsApp", "Address"])
                search_value = st.text_input(f"Enter {search_type}", placeholder=f"Search by {search_type.lower()}")
                
                devotees = safe_query("devotees")
                
                if search_value:
                    if search_type == "Name":
                        devotees = [d for d in devotees if search_value.lower() in d.get('name', '').lower()]
                    elif search_type == "Mobile":
                        devotees = [d for d in devotees if search_value in d.get('mobile_no', '')]
                    elif search_type == "WhatsApp":
                        devotees = [d for d in devotees if search_value in d.get('whatsapp_no', '')]
                    elif search_type == "Address":
                        devotees = [d for d in devotees if search_value.lower() in d.get('address', '').lower()]
                
                if devotees:
                    devotee_display = {f"{d['name']} - {d.get('mobile_no', 'N/A')} - {d.get('address', 'N/A')[:30]}": d for d in devotees}
                    selected = st.selectbox("Select Devotee", list(devotee_display.keys()))
                    
                    if selected:
                        sel_devotee = devotee_display[selected]
                        devotee_id = sel_devotee['id']
                        
                        st.markdown(f"""
                        <div class="success-box">
                            <strong>Selected Devotee:</strong><br>
                            👤 {sel_devotee['name']}<br>
                            📱 {sel_devotee.get('mobile_no', 'N/A')}<br>
                            📲 {sel_devotee.get('whatsapp_no', 'N/A')}<br>
                            🏠 {sel_devotee.get('address', 'N/A')}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.warning("No devotees found matching your search")
            
            else:  # Guest Devotee
                st.markdown("### 👤 Guest Details")
                guest_name = st.text_input("👤 Guest Name *", placeholder="Enter guest name")
                guest_address = st.text_area("🏠 Guest Address *", placeholder="Enter guest address")
                guest_mobile = st.text_input("📱 Mobile Number", placeholder="Enter mobile number")
                guest_whatsapp = st.text_input("📲 WhatsApp Number", placeholder="Enter WhatsApp number")
        
        # Generate Bill Button
        if st.button("🧾 Generate Bill", use_container_width=True, type="primary"):
            if devotee_type == "Enrolled Devotee" and not devotee_id:
                st.error("❌ Please select an enrolled devotee!")
            elif devotee_type == "Guest Devotee" and not guest_name:
                st.error("❌ Please enter guest name!")
            elif amount <= 0:
                st.error("❌ Amount must be greater than 0!")
            else:
                bill_no = generate_bill_no()
                pooja_name = selected_pooja.split(" - ")[0] if " - " in selected_pooja else selected_pooja
                
                bill_data = {
                    "bill_no": bill_no,
                    "manual_bill_no": manual_bill_no,
                    "bill_book_no": bill_book_no,
                    "devotee_type": "enrolled" if devotee_type == "Enrolled Devotee" else "guest",
                    "devotee_id": devotee_id,
                    "guest_name": guest_name if devotee_type == "Guest Devotee" else None,
                    "guest_address": guest_address if devotee_type == "Guest Devotee" else None,
                    "guest_mobile": guest_mobile if devotee_type == "Guest Devotee" else None,
                    "guest_whatsapp": guest_whatsapp if devotee_type == "Guest Devotee" else None,
                    "pooja_type": pooja_name,
                    "amount": amount,
                    "bill_date": str(bill_date)
                }
                
                result = safe_insert("bills", bill_data)
                if result:
                    st.success(f"✅ Bill generated successfully! Bill No: {bill_no}")
                    
                    # Display Bill
                    st.markdown("---")
                    st.markdown("### 🧾 Bill Preview")
                    
                    if devotee_type == "Enrolled Devotee" and devotee_id:
                        dev = [d for d in safe_query("devotees") if d['id'] == devotee_id]
                        if dev:
                            bname = dev[0]['name']
                            baddress = dev[0].get('address', '')
                            bmobile = dev[0].get('mobile_no', '')
                        else:
                            bname = baddress = bmobile = "N/A"
                    else:
                        bname = guest_name
                        baddress = guest_address
                        bmobile = guest_mobile
                    
                    st.markdown(f"""
                    <div style="background:white; padding:30px; border:2px solid #ff6b35; border-radius:15px; max-width:500px; margin:auto;">
                        <div style="text-align:center; border-bottom:2px solid #ff6b35; padding-bottom:15px;">
                            <h2 style="color:#8B0000; margin:0;">🛕 Temple Name</h2>
                            <p style="margin:5px 0;">Temple Address Line</p>
                        </div>
                        <div style="padding:15px 0;">
                            <table style="width:100%;">
                                <tr><td><strong>Bill No:</strong></td><td>{bill_no}</td></tr>
                                <tr><td><strong>Manual Bill No:</strong></td><td>{manual_bill_no}</td></tr>
                                <tr><td><strong>Bill Book No:</strong></td><td>{bill_book_no}</td></tr>
                                <tr><td><strong>Date:</strong></td><td>{bill_date}</td></tr>
                                <tr><td colspan="2"><hr></td></tr>
                                <tr><td><strong>Name:</strong></td><td>{bname}</td></tr>
                                <tr><td><strong>Address:</strong></td><td>{baddress}</td></tr>
                                <tr><td><strong>Mobile:</strong></td><td>{bmobile}</td></tr>
                                <tr><td colspan="2"><hr></td></tr>
                                <tr><td><strong>Pooja Type:</strong></td><td>{pooja_name}</td></tr>
                                <tr><td><strong>Amount:</strong></td><td style="font-size:1.3em; color:#11998e;"><strong>₹ {amount:,.2f}</strong></td></tr>
                            </table>
                        </div>
                        <div style="text-align:center; border-top:2px solid #ff6b35; padding-top:10px;">
                            <p style="margin:0; color:#666;">🙏 Thank you for your contribution! 🙏</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    
    # --- TAB 2: Bill History ---
    with tab2:
        st.markdown("### 📋 Bill History")
        
        bills = safe_query("bills")
        
        if bills:
            bills_sorted = sorted(bills, key=lambda x: x.get('created_at', ''), reverse=True)
            
            for bill in bills_sorted:
                bill_name = bill.get('guest_name', '')
                if bill.get('devotee_type') == 'enrolled' and bill.get('devotee_id'):
                    dev_data = safe_query("devotees", filters={"id": bill['devotee_id']})
                    if dev_data:
                        bill_name = dev_data[0]['name']
                
                with st.expander(f"🧾 {bill.get('bill_no', 'N/A')} | {bill_name} | {bill.get('pooja_type', '')} | ₹{bill.get('amount', 0)} | {bill.get('bill_date', '')}"):
                    st.write(f"**Bill No:** {bill.get('bill_no', 'N/A')}")
                    st.write(f"**Manual Bill No:** {bill.get('manual_bill_no', 'N/A')}")
                    st.write(f"**Bill Book No:** {bill.get('bill_book_no', 'N/A')}")
                    st.write(f"**Type:** {bill.get('devotee_type', 'N/A')}")
                    st.write(f"**Pooja:** {bill.get('pooja_type', 'N/A')}")
                    st.write(f"**Amount:** ₹{bill.get('amount', 0)}")
                    st.write(f"**Date:** {bill.get('bill_date', 'N/A')}")
                    
                    if bill.get('devotee_type') == 'guest':
                        st.write(f"**Guest Name:** {bill.get('guest_name', 'N/A')}")
                        st.write(f"**Guest Address:** {bill.get('guest_address', 'N/A')}")
                        st.write(f"**Guest Mobile:** {bill.get('guest_mobile', 'N/A')}")
                    
                    # Delete button (admin only)
                    if st.session_state.user_role == 'admin':
                        if st.button(f"🗑️ Delete Bill", key=f"del_bill_{bill['id']}"):
                            safe_delete("bills", "id", bill['id'])
                            st.success("✅ Bill deleted!")
                            st.rerun()
        else:
            st.info("No bills found")

# ============================================================
# EXPENSES PAGE
# ============================================================
def expenses_page():
    st.markdown("""
    <div class="main-header">
        <h1>💸 Expenses Management</h1>
        <p>Track and manage temple expenses</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["➕ Add Expense", "📋 Expense History"])
    
    with tab1:
        with st.form("expense_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                expense_types = safe_query("expense_types")
                exp_names = [e['name'] for e in expense_types] if expense_types else ["Miscellaneous"]
                expense_type = st.selectbox("📂 Expense Type", exp_names)
                amount = st.number_input("💰 Amount (₹)", min_value=0.0, step=10.0)
            
            with col2:
                expense_date = st.date_input("📅 Date", value=date.today())
                description = st.text_area("📝 Description", placeholder="Enter expense details")
            
            if st.form_submit_button("💾 Save Expense", use_container_width=True):
                if amount > 0:
                    safe_insert("expenses", {
                        "expense_type": expense_type,
                        "amount": amount,
                        "description": description,
                        "expense_date": str(expense_date)
                    })
                    st.success("✅ Expense recorded successfully!")
                    st.rerun()
                else:
                    st.error("❌ Amount must be greater than 0!")
    
    with tab2:
        expenses = safe_query("expenses")
        if expenses:
            expenses_sorted = sorted(expenses, key=lambda x: x.get('expense_date', ''), reverse=True)
            
            # Summary
            total_exp = sum(float(e.get('amount', 0)) for e in expenses)
            st.metric("Total Expenses", f"₹ {total_exp:,.2f}")
            
            # Table
            df = pd.DataFrame([{
                "Date": e.get('expense_date', ''),
                "Type": e.get('expense_type', ''),
                "Amount": f"₹ {e.get('amount', 0):,.2f}",
                "Description": e.get('description', '')
            } for e in expenses_sorted])
            
            st.dataframe(df, use_container_width=True)
            
            # Delete option
            if st.session_state.user_role == 'admin':
                st.markdown("### 🗑️ Delete Expense")
                exp_options = {f"{e.get('expense_date', '')} - {e.get('expense_type', '')} - ₹{e.get('amount', 0)}": e['id'] for e in expenses_sorted}
                sel_exp = st.selectbox("Select expense to delete", list(exp_options.keys()))
                if st.button("🗑️ Delete Selected Expense"):
                    safe_delete("expenses", "id", exp_options[sel_exp])
                    st.success("✅ Expense deleted!")
                    st.rerun()
        else:
            st.info("No expenses recorded yet")

# ============================================================
# REPORTS PAGE
# ============================================================
def reports_page():
    st.markdown("""
    <div class="main-header">
        <h1>📊 Reports</h1>
        <p>Financial and operational reports</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Filter Options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        report_period = st.selectbox("📅 Report Period", ["Daily", "Weekly", "Monthly", "Yearly", "Custom Date"])
    
    today = date.today()
    
    if report_period == "Custom Date":
        with col2:
            custom_start = st.date_input("Start Date", value=today - timedelta(days=30))
        with col3:
            custom_end = st.date_input("End Date", value=today)
        start_date = custom_start
        end_date = custom_end
    elif report_period == "Daily":
        start_date = today
        end_date = today
    elif report_period == "Weekly":
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif report_period == "Monthly":
        start_date = today.replace(day=1)
        end_date = today
    else:
        start_date = today.replace(month=1, day=1)
        end_date = today
    
    with col3 if report_period != "Custom Date" else st.columns(1)[0]:
        pooja_types = safe_query("pooja_types")
        pt_names = ["All"] + [p['name'] for p in pooja_types] if pooja_types else ["All"]
        pooja_filter = st.selectbox("🙏 Pooja Type Filter", pt_names)
    
    st.markdown("---")
    
    # Fetch Data
    try:
        bills_result = supabase.table("bills").select("*").gte("bill_date", str(start_date)).lte("bill_date", str(end_date)).execute()
        bills_data = bills_result.data if bills_result.data else []
        
        expenses_result = supabase.table("expenses").select("*").gte("expense_date", str(start_date)).lte("expense_date", str(end_date)).execute()
        expenses_data = expenses_result.data if expenses_result.data else []
    except:
        bills_data = []
        expenses_data = []
    
    # Apply pooja filter
    if pooja_filter != "All":
        bills_data = [b for b in bills_data if b.get('pooja_type') == pooja_filter]
    
    total_income = sum(float(b.get('amount', 0)) for b in bills_data)
    total_expenses = sum(float(e.get('amount', 0)) for e in expenses_data)
    net_balance = total_income - total_expenses
    
    # Summary Cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card income">
            <h3>💰 Total Income</h3>
            <h2>₹ {total_income:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card expense">
            <h3>💸 Total Expenses</h3>
            <h2>₹ {total_expenses:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card balance">
            <h3>💎 Net Balance</h3>
            <h2>₹ {net_balance:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Income Report
    report_tab1, report_tab2, report_tab3 = st.tabs(["💰 Income Report", "💸 Expense Report", "📈 Charts"])
    
    with report_tab1:
        if bills_data:
            df_income = pd.DataFrame([{
                "Bill No": b.get('bill_no', ''),
                "Manual Bill No": b.get('manual_bill_no', ''),
                "Date": b.get('bill_date', ''),
                "Pooja Type": b.get('pooja_type', ''),
                "Devotee Type": b.get('devotee_type', ''),
                "Amount": float(b.get('amount', 0))
            } for b in bills_data])
            
            st.dataframe(df_income, use_container_width=True)
            
            # Pooja-wise summary
            st.markdown("### Pooja-wise Summary")
            pooja_summary = df_income.groupby('Pooja Type')['Amount'].agg(['sum', 'count']).reset_index()
            pooja_summary.columns = ['Pooja Type', 'Total Amount', 'Count']
            st.dataframe(pooja_summary, use_container_width=True)
            
            # Download
            csv = df_income.to_csv(index=False)
            st.download_button("📥 Download Income Report", csv, "income_report.csv", "text/csv")
        else:
            st.info("No income data for selected period")
    
    with report_tab2:
        if expenses_data:
            df_expenses = pd.DataFrame([{
                "Date": e.get('expense_date', ''),
                "Type": e.get('expense_type', ''),
                "Amount": float(e.get('amount', 0)),
                "Description": e.get('description', '')
            } for e in expenses_data])
            
            st.dataframe(df_expenses, use_container_width=True)
            
            # Type-wise summary
            st.markdown("### Expense Type-wise Summary")
            exp_summary = df_expenses.groupby('Type')['Amount'].agg(['sum', 'count']).reset_index()
            exp_summary.columns = ['Expense Type', 'Total Amount', 'Count']
            st.dataframe(exp_summary, use_container_width=True)
            
            csv = df_expenses.to_csv(index=False)
            st.download_button("📥 Download Expense Report", csv, "expense_report.csv", "text/csv")
        else:
            st.info("No expense data for selected period")
    
    with report_tab3:
        if bills_data or expenses_data:
            # Income vs Expenses Bar
            chart_df = pd.DataFrame({
                "Category": ["Income", "Expenses"],
                "Amount": [total_income, total_expenses]
            })
            st.bar_chart(chart_df.set_index("Category"))
            
            # Daily trend
            if bills_data:
                daily_income = {}
                for b in bills_data:
                    d = b.get('bill_date', '')
                    daily_income[d] = daily_income.get(d, 0) + float(b.get('amount', 0))
                
                if daily_income:
                    trend_df = pd.DataFrame(list(daily_income.items()), columns=["Date", "Income"])
                    trend_df = trend_df.sort_values("Date")
                    st.line_chart(trend_df.set_index("Date"))
        else:
            st.info("No data available for charts")

# ============================================================
# SETTINGS PAGE
# ============================================================
def settings_page():
    st.markdown("""
    <div class="main-header">
        <h1>⚙️ Settings</h1>
        <p>Configure pooja types, expense types, and news ticker</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🙏 Pooja Types", "💸 Expense Types", "📢 News Ticker"])
    
    # --- Pooja Types ---
    with tab1:
        st.markdown("### 🙏 Manage Pooja Types")
        
        pooja_types = safe_query("pooja_types")
        
        if pooja_types:
            for pt in pooja_types:
                pt_col1, pt_col2, pt_col3 = st.columns([3, 1, 1])
                with pt_col1:
                    st.write(f"🙏 **{pt['name']}** - ₹{pt.get('amount', 0)}")
                with pt_col3:
                    if st.button("🗑️", key=f"del_pt_{pt['id']}"):
                        safe_delete("pooja_types", "id", pt['id'])
                        st.success("Deleted!")
                        st.rerun()
        
        st.markdown("---")
        with st.form("add_pooja_type", clear_on_submit=True):
            pt_col1, pt_col2 = st.columns(2)
            with pt_col1:
                new_pt_name = st.text_input("Pooja Type Name")
            with pt_col2:
                new_pt_amount = st.number_input("Default Amount (₹)", min_value=0.0, step=10.0)
            
            if st.form_submit_button("➕ Add Pooja Type"):
                if new_pt_name:
                    safe_insert("pooja_types", {"name": new_pt_name, "amount": new_pt_amount})
                    st.success(f"✅ Pooja type '{new_pt_name}' added!")
                    st.rerun()
    
    # --- Expense Types ---
    with tab2:
        st.markdown("### 💸 Manage Expense Types")
        
        expense_types = safe_query("expense_types")
        
        if expense_types:
            for et in expense_types:
                et_col1, et_col2 = st.columns([4, 1])
                with et_col1:
                    st.write(f"💸 **{et['name']}**")
                with et_col2:
                    if st.button("🗑️", key=f"del_et_{et['id']}"):
                        safe_delete("expense_types", "id", et['id'])
                        st.success("Deleted!")
                        st.rerun()
        
        st.markdown("---")
        with st.form("add_expense_type", clear_on_submit=True):
            new_et_name = st.text_input("Expense Type Name")
            if st.form_submit_button("➕ Add Expense Type"):
                if new_et_name:
                    safe_insert("expense_types", {"name": new_et_name})
                    st.success(f"✅ Expense type '{new_et_name}' added!")
                    st.rerun()
    
    # --- News Ticker ---
    with tab3:
        st.markdown("### 📢 Manage News Ticker")
        
        news_items = safe_query("news_ticker")
        
        if news_items:
            for n in news_items:
                n_col1, n_col2, n_col3 = st.columns([4, 1, 1])
                with n_col1:
                    status = "🟢" if n.get('is_active') else "🔴"
                    st.write(f"{status} {n['message']}")
                with n_col2:
                    if st.button("Toggle", key=f"toggle_n_{n['id']}"):
                        safe_update("news_ticker", {"is_active": not n.get('is_active', True)}, "id", n['id'])
                        st.rerun()
                with n_col3:
                    if st.button("🗑️", key=f"del_n_{n['id']}"):
                        safe_delete("news_ticker", "id", n['id'])
                        st.rerun()
        
        st.markdown("---")
        with st.form("add_news", clear_on_submit=True):
            new_message = st.text_input("News Message")
            if st.form_submit_button("➕ Add News"):
                if new_message:
                    safe_insert("news_ticker", {"message": new_message, "is_active": True})
                    st.success("✅ News added!")
                    st.rerun()

# ============================================================
# USER CREATION PAGE
# ============================================================
def user_creation_page():
    st.markdown("""
    <div class="main-header">
        <h1>👥 User Management</h1>
        <p>Create and manage system users</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.user_role != 'admin':
        st.error("❌ Only admin can manage users!")
        return
    
    tab1, tab2 = st.tabs(["➕ Create User", "📋 Manage Users"])
    
    with tab1:
        with st.form("create_user", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                new_username = st.text_input("👤 Username")
                new_password = st.text_input("🔑 Password", type="password")
            with col2:
                confirm_password = st.text_input("🔑 Confirm Password", type="password")
                new_role = st.selectbox("🎭 Role", ["user", "admin"])
            
            if st.form_submit_button("➕ Create User", use_container_width=True):
                if not new_username or not new_password:
                    st.error("❌ Username and password are required!")
                elif new_password != confirm_password:
                    st.error("❌ Passwords don't match!")
                else:
                    existing = safe_query("users", filters={"username": new_username})
                    if existing:
                        st.error("❌ Username already exists!")
                    else:
                        safe_insert("users", {
                            "username": new_username,
                            "password_hash": new_password,
                            "role": new_role
                        })
                        st.success(f"✅ User '{new_username}' created successfully!")
                        st.rerun()
    
    with tab2:
        users = safe_query("users")
        if users:
            for u in users:
                u_col1, u_col2 = st.columns([4, 1])
                with u_col1:
                    role_icon = "👑" if u.get('role') == 'admin' else "👤"
                    st.write(f"{role_icon} **{u['username']}** ({u.get('role', 'user')})")
                with u_col2:
                    if u['username'] != 'admin':
                        if st.button("🗑️", key=f"del_user_{u['id']}"):
                            safe_delete("users", "id", u['id'])
                            st.success("✅ User deleted!")
                            st.rerun()

# ============================================================
# SAMAYA VAKUPPU PAGE
# ============================================================
def samaya_vakuppu_page():
    st.markdown("""
    <div class="main-header">
        <h1>📚 Samaya Vakuppu</h1>
        <p>Religious education student management</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["➕ Add Student", "📋 Student List"])
    
    with tab1:
        with st.form("samaya_vakuppu_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                sv_name = st.text_input("👤 Student Name *")
                sv_dob = st.date_input("📅 Date of Birth", value=date(2010, 1, 1))
                sv_address = st.text_area("🏠 Address")
                sv_parent_type = st.selectbox("👪 Parent Type", ["Father", "Mother"])
                sv_parent_name = st.text_input("👤 Parent Name")
            
            with col2:
                sv_bond_issue_date = st.date_input("📅 Bond Issue Date", value=date.today())
                sv_bond_bank = st.text_input("🏦 Bond Issuing Bank")
                sv_bond_branch = st.text_input("🏦 Branch of Bank")
                sv_bond_no = st.text_input("📋 Bond Number")
                sv_scanned_bond = st.file_uploader("📄 Upload Scanned Bond", type=['jpg', 'jpeg', 'png', 'pdf'], key="sv_bond")
                sv_photo = st.file_uploader("📷 Upload Photo", type=['jpg', 'jpeg', 'png'], key="sv_photo")
            
            if st.form_submit_button("✅ Register Student", use_container_width=True):
                if sv_name:
                    bond_url = None
                    photo_url = None
                    
                    if sv_scanned_bond:
                        bond_url = upload_to_supabase_storage(sv_scanned_bond, "bonds", f"samaya/{sv_name}_bond")
                    if sv_photo:
                        photo_url = upload_to_supabase_storage(sv_photo, "photos", f"samaya/{sv_name}_photo")
                    
                    safe_insert("samaya_vakuppu", {
                        "student_name": sv_name,
                        "dob": str(sv_dob),
                        "address": sv_address,
                        "parent_name": sv_parent_name,
                        "parent_type": sv_parent_type,
                        "bond_issue_date": str(sv_bond_issue_date),
                        "scanned_bond_url": bond_url,
                        "photo_url": photo_url,
                        "bond_issuing_bank": sv_bond_bank,
                        "branch_of_bank": sv_bond_branch,
                        "bond_no": sv_bond_no
                    })
                    st.success(f"✅ Student '{sv_name}' registered successfully!")
                    st.rerun()
                else:
                    st.error("❌ Student name is required!")
    
    with tab2:
        students = safe_query("samaya_vakuppu")
        
        if students:
            search_student = st.text_input("🔍 Search Student", placeholder="Enter name to search")
            
            if search_student:
                students = [s for s in students if search_student.lower() in s.get('student_name', '').lower()]
            
            for s in students:
                with st.expander(f"👤 {s['student_name']} | Bond: {s.get('bond_no', 'N/A')}"):
                    s_col1, s_col2 = st.columns([3, 1])
                    
                    with s_col1:
                        st.write(f"**Name:** {s['student_name']}")
                        st.write(f"**DOB:** {s.get('dob', 'N/A')}")
                        st.write(f"**Address:** {s.get('address', 'N/A')}")
                        st.write(f"**{s.get('parent_type', 'Parent')}:** {s.get('parent_name', 'N/A')}")
                        st.write(f"**Bond Issue Date:** {s.get('bond_issue_date', 'N/A')}")
                        st.write(f"**Bank:** {s.get('bond_issuing_bank', 'N/A')}")
                        st.write(f"**Branch:** {s.get('branch_of_bank', 'N/A')}")
                        st.write(f"**Bond No:** {s.get('bond_no', 'N/A')}")
                    
                    with s_col2:
                        if s.get('photo_url') and s['photo_url'].startswith('data:'):
                            st.markdown(f'<img src="{s["photo_url"]}" width="120" style="border-radius:10px;">', unsafe_allow_html=True)
                    
                    if st.button(f"🗑️ Delete", key=f"del_sv_{s['id']}"):
                        safe_delete("samaya_vakuppu", "id", s['id'])
                        st.success("✅ Student deleted!")
                        st.rerun()
        else:
            st.info("No students registered yet")

# ============================================================
# THIRUMANA MANDAPAM PAGE
# ============================================================
def thirumana_mandapam_page():
    st.markdown("""
    <div class="main-header">
        <h1>💒 Thirumana Mandapam</h1>
        <p>Marriage hall booking and bond management</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["➕ Add Record", "📋 Records List"])
    
    with tab1:
        with st.form("thirumana_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                tm_name = st.text_input("👤 Name *")
                tm_address = st.text_area("🏠 Address")
                tm_bond_no = st.text_input("📋 Bond Number")
                tm_bond_date = st.date_input("📅 Bond Issued Date", value=date.today())
            
            with col2:
                tm_amount = st.number_input("💰 Amount (₹)", min_value=0.0, step=100.0)
                tm_no_bonds = st.number_input("📋 Number of Bonds", min_value=0, step=1)
                tm_scan = st.file_uploader("📄 Scan Copy of Bond", type=['jpg', 'jpeg', 'png', 'pdf'], key="tm_scan")
                tm_photo = st.file_uploader("📷 Photo", type=['jpg', 'jpeg', 'png'], key="tm_photo")
            
            if st.form_submit_button("✅ Save Record", use_container_width=True):
                if tm_name:
                    scan_url = None
                    photo_url = None
                    
                    if tm_scan:
                        scan_url = upload_to_supabase_storage(tm_scan, "bonds", f"thirumana/{tm_name}_scan")
                    if tm_photo:
                        photo_url = upload_to_supabase_storage(tm_photo, "photos", f"thirumana/{tm_name}_photo")
                    
                    safe_insert("thirumana_mandapam", {
                        "name": tm_name,
                        "address": tm_address,
                        "bond_no": tm_bond_no,
                        "bond_issued_date": str(tm_bond_date),
                        "amount": tm_amount,
                        "no_of_bonds": tm_no_bonds,
                        "scan_copy_url": scan_url,
                        "photo_url": photo_url
                    })
                    st.success(f"✅ Record for '{tm_name}' saved successfully!")
                    st.rerun()
                else:
                    st.error("❌ Name is required!")
    
    with tab2:
        records = safe_query("thirumana_mandapam")
        
        if records:
            search_tm = st.text_input("🔍 Search Records", placeholder="Enter name to search")
            
            if search_tm:
                records = [r for r in records if search_tm.lower() in r.get('name', '').lower()]
            
            for r in records:
                with st.expander(f"👤 {r['name']} | Bond: {r.get('bond_no', 'N/A')} | ₹{r.get('amount', 0)}"):
                    r_col1, r_col2 = st.columns([3, 1])
                    
                    with r_col1:
                        st.write(f"**Name:** {r['name']}")
                        st.write(f"**Address:** {r.get('address', 'N/A')}")
                        st.write(f"**Bond No:** {r.get('bond_no', 'N/A')}")
                        st.write(f"**Bond Issued Date:** {r.get('bond_issued_date', 'N/A')}")
                        st.write(f"**Amount:** ₹{r.get('amount', 0):,.2f}")
                        st.write(f"**No. of Bonds:** {r.get('no_of_bonds', 'N/A')}")
                    
                    with r_col2:
                        if r.get('photo_url') and r['photo_url'].startswith('data:'):
                            st.markdown(f'<img src="{r["photo_url"]}" width="120" style="border-radius:10px;">', unsafe_allow_html=True)
                    
                    if st.button(f"🗑️ Delete", key=f"del_tm_{r['id']}"):
                        safe_delete("thirumana_mandapam", "id", r['id'])
                        st.success("✅ Record deleted!")
                        st.rerun()
        else:
            st.info("No records found")

# ============================================================
# SIDEBAR NAVIGATION
# ============================================================
def sidebar_navigation():
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align:center; padding:15px; background:linear-gradient(135deg, #ff6b35, #f7c948); border-radius:10px; margin-bottom:15px;">
            <h2 style="color:#8B0000; margin:0;">🛕</h2>
            <p style="color:#5a1a00; margin:5px 0 0 0; font-weight:600;">Temple Management</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"👤 **{st.session_state.username}** ({st.session_state.user_role})")
        st.markdown("---")
        
        menu_items = {
            "🏠 Dashboard": "Dashboard",
            "👥 Devotee Enrollment": "Devotee Enrollment",
            "🧾 Billing": "Billing",
            "💸 Expenses": "Expenses",
            "📊 Reports": "Reports",
            "📚 Samaya Vakuppu": "Samaya Vakuppu",
            "💒 Thirumana Mandapam": "Thirumana Mandapam",
            "⚙️ Settings": "Settings",
            "👥 User Management": "User Management"
        }
        
        for label, page in menu_items.items():
            if page == "User Management" and st.session_state.user_role != 'admin':
                continue
            if st.button(label, key=f"nav_{page}", use_container_width=True):
                st.session_state.current_page = page
                st.rerun()
        
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.user_role = ""
            st.session_state.current_page = "Dashboard"
            st.rerun()

# ============================================================
# MAIN APPLICATION ROUTER
# ============================================================
def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        sidebar_navigation()
        
        page = st.session_state.current_page
        
        if page == "Dashboard":
            dashboard_page()
        elif page == "Devotee Enrollment":
            devotee_enrollment_page()
        elif page == "Billing":
            billing_page()
        elif page == "Expenses":
            expenses_page()
        elif page == "Reports":
            reports_page()
        elif page == "Samaya Vakuppu":
            samaya_vakuppu_page()
        elif page == "Thirumana Mandapam":
            thirumana_mandapam_page()
        elif page == "Settings":
            settings_page()
        elif page == "User Management":
            user_creation_page()

if __name__ == "__main__":
    main()
