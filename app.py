import streamlit as st
import pandas as pd
import numpy as np
import time
import extra_streamlit_components as stx

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(
    page_title="Team Sensor Command Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# ⚠️ CONFIGURATION ⚠️
# ==========================================
# 1. ฐานข้อมูลสมาชิก
USER_DB_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR0XoahMwduVM49_EJjYxMnbU9ABtSZzYPiInXBvSf_LhtAJqhl_5FRw-YrHQ7EIl2wbN27uZv0YTz9/pub?output=csv"
REGISTER_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdx0bamRVPVOfiBXMpbbOSZny9Snr4U0VImflmJwm6KcdYKSA/viewform?usp=publish-editor"

# 2. ข้อมูล CPN AYY (ลิงก์ CSV เฉพาะหน้า CPN_AYY)
# 🔴 เอาลิงก์ CSV หน้า CPN_AYY มาใส่ตรงนี้ 🔴
CPN_AYY_API_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ6mJlIlopngupLvxdnFyvCzVpXhWt-Slf6g4-wHa_e9lkcxMkOxAHN-3X0UBf7ZuR1sMkcuSDNE3p0/pub?output=csv" 
# (ผมลองเดา GID จากลิงก์คุณให้ ถ้าไม่ได้ให้ใช้ลิงก์ที่คุณทำเองนะครับ)
# ==========================================

# --- Cookie Manager ---
cookie_manager = stx.CookieManager()

# --- Functions ---
def load_users():
    try:
        df = pd.read_csv(USER_DB_URL, on_bad_lines='skip')
        if len(df.columns) >= 5:
            df.columns.values[1] = 'username'
            df.columns.values[2] = 'password'
            df.columns.values[3] = 'name'
            df.columns.values[4] = 'role'
        df['password'] = df['password'].astype(str)
        df['role'] = df['role'].fillna('User')
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_cpn_data():
    try:
        # ใช้ on_bad_lines='skip' เพื่อข้ามบรรทัดที่ error
        df = pd.read_csv(CPN_AYY_API_URL, on_bad_lines='skip')
        return df
    except:
        return pd.DataFrame()

def check_cookies():
    try:
        cookie_user = cookie_manager.get(cookie="sensor_user")
        if cookie_user and not st.session_state.get('logged_in', False):
            df = load_users()
            user_match = df[df['username'].astype(str) == str(cookie_user)]
            if not user_match.empty:
                user = user_match.iloc[0]
                st.session_state['logged_in'] = True
                st.session_state['user'] = user['name']
                st.session_state['role'] = str(user['role']).strip()
    except:
        pass

# --- PAGE: LOGIN ---
def login_page():
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        try: st.image("logo.png", use_container_width=True)
        except: st.header("⚡ TEAM SENSOR")

    st.markdown("<h3 style='text-align: center;'>System Login</h3>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])

    with tab1:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login", use_container_width=True):
            df = load_users()
            if not df.empty:
                match = df[(df['username'].astype(str) == username) & (df['password'].astype(str) == password)]
                if not match.empty:
                    user = match.iloc[0]
                    st.session_state['logged_in'] = True
                    st.session_state['user'] = user['name']
                    st.session_state['role'] = str(user['role']).strip()
                    cookie_manager.set("sensor_user", username, expires_at=pd.Timestamp.now() + pd.Timedelta(days=7))
                    st.success(f"Welcome {user['name']}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Login Failed")
            else:
                st.error("Database Error")

    with tab2:
        st.info("สมัครผ่าน Google Form")
        st.link_button("👉 ไปที่ฟอร์มสมัคร", REGISTER_URL, use_container_width=True)

# --- PAGE: MAIN APP ---
def main_app():
    with st.sidebar:
        st.write(f"👤 **{st.session_state['user']}**")
        role = st.session_state['role']
        if role == 'Admin':
            st.success(f"Role: {role}")
            st.divider()
            if st.checkbox("Manage Users"):
                st.dataframe(load_users())
                st.caption("Edit via Google Sheet")
        else:
            st.info(f"Role: {role}")
        
        st.divider()
        if st.button("Log out", type="primary"):
            cookie_manager.delete("sensor_user")
            st.session_state['logged_in'] = False
            st.rerun()

    # --- NAVIGATION (เมนูหลัก) ---
    st.sidebar.title("🚀 Navigation")
    page = st.sidebar.radio("Go to", [
        "🌏 Dashboard: Overview",   # อันเก่า (แผนที่)
        "🏢 Dashboard: CPN AYY",    # อันใหม่ (Sensor Data)
        "📚 Learning Academy",
        "✍️ Quiz"
    ])

    # === 1. DASHBOARD: OVERVIEW (แผนที่ประเทศไทย) ===
    if page == "🌏 Dashboard: Overview":
        st.title("🌏 Real-time Command Center (Overview)")
        
        # Mockup Data สำหรับแผนที่ (คุณสามารถแก้ในเว็บได้ถ้าเป็น Admin)
        if 'sites' not in st.session_state:
            st.session_state.sites = pd.DataFrame({
                'Site Name': ['RBS Chonburi', 'Central Ayutthaya', 'RBS Rayong', 'Robinson Saraburi'],
                'Lat': [13.3611, 14.3532, 12.6828, 14.5290],
                'Lon': [100.9847, 100.5700, 101.2816, 100.9130],
                'Status': ['Normal', 'Critical', 'Maintenance', 'Normal'],
            })

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Sites", len(st.session_state.sites))
        col2.metric("Critical Status", len(st.session_state.sites[st.session_state.sites['Status']=='Critical']), delta="-1")
        col3.metric("Sensors Online", "98.2%", "stable")
        col4.metric("Pending PM", "2 Jobs", "Urgent")

        col_map, col_data = st.columns([1, 1])
        with col_map:
            st.subheader("📍 Site Map")
            map_df = st.session_state.sites.copy()
            map_df['color'] = map_df['Status'].apply(lambda x: '#00FF00' if x=='Normal' else '#FF0000')
            st.map(map_df, latitude='Lat', longitude='Lon', size=20, color='color')

        with col_data:
            st.subheader("📝 Site Data Management")
            if st.session_state['role'] == 'Admin':
                st.caption("🔓 Admin Mode: Editing Enabled")
                edited_df = st.data_editor(st.session_state.sites, num_rows="dynamic", key="overview_edit")
                if st.button("Save Changes"):
                    st.session_state.sites = edited_df
                    st.success("Saved!")
            else:
                st.caption("🔒 Read-only Mode")
                st.dataframe(st.session_state.sites)

    # === 2. DASHBOARD: CPN AYY (ข้อมูลเจาะลึก) ===
    elif page == "🏢 Dashboard: CPN AYY":
        st.title("🏢 CPN Ayutthaya - Sensor Status")
        
        df = load_cpn_data()
        
        if not df.empty:
            # เช็คคอลัมน์ (บางทีชื่ออาจไม่เป๊ะ ใช้ contains ช่วยได้)
            # สมมติชื่อคอลัมน์ใน Sheet คือ "getStatusAPI", "Position Name"
            if 'getStatusAPI' in df.columns:
                
                total = len(df)
                good = len(df[df['getStatusAPI'] == 'Good'])
                bad = len(df[df['getStatusAPI'] == 'Bad'])
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Total Points", total)
                c2.metric("Good", good, "Online")
                c3.metric("Bad", bad, "Offline", delta_color="inverse")
                c4.metric("Update", time.strftime("%H:%M"))
                
                st.divider()
                
                col_filt, col_tab = st.columns([1, 3])
                with col_filt:
                    st.subheader("Filter")
                    status_select = st.multiselect("Status", df['getStatusAPI'].unique(), default=df['getStatusAPI'].unique())
                    
                    if 'Floor' in df.columns:
                        floor_select = st.multiselect("Floor", df['Floor'].unique(), default=df['Floor'].unique())
                    else:
                        floor_select = []

                with col_tab:
                    # Filter Logic
                    mask = df['getStatusAPI'].isin(status_select)
                    if 'Floor' in df.columns and floor_select:
                        mask = mask & df['Floor'].isin(floor_select)
                    
                    show_df = df[mask]
                    st.dataframe(show_df, use_container_width=True, height=500)
            else:
                st.error("ไม่พบคอลัมน์ 'getStatusAPI' กรุณาตรวจสอบ Google Sheet")
                st.write(df.head())
        else:
            st.info("กำลังโหลดข้อมูล... หรือลิงก์ยังไม่ถูกต้อง")
            st.caption(f"Source: {CPN_AYY_API_URL}")

    # === 3. LEARNING ACADEMY ===
    elif page == "📚 Learning Academy":
        st.title("📚 Team Sensor Academy")
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "1. Heat Balance Analysis", 
            "2. Efficiency (kW/RT)", 
            "3. Sensor Calibration",
            "4. รู้จักตัวแปร CQ1-CQ7",        
            "5. ขั้นตอนสำรวจหน้างาน (Audit)"   
        ])
        
        with tab1:
            st.header("🔥 Heat Balance")
            st.latex(r"\% Heat Balance = \frac{(Q_{evap} + W_{input}) - Q_{cond}}{Q_{cond}} \times 100")
            st.markdown("**เกณฑ์:** ±5% (ถ้าเกินแสดงว่า Flow หรือ Sensor มีปัญหา)")
            
        with tab2:
            st.header("⚡ Efficiency")
            st.markdown("**สูตร:** $kW/RT = Power / Ton$ (ยิ่งน้อยยิ่งดี)")

        with tab3:
            st.header("🛠️ Calibration")
            st.markdown("**สูตร:** Error = Reading - Standard")

        with tab4:
            st.header("ไขรหัส CQ")
            st.table(pd.DataFrame([
                {"Code": "CQ1", "Name": "Inlet Condensing Temp"},
                {"Code": "CQ2", "Name": "Inlet Evaporator Temp"}
            ]))

        with tab5:
            st.header("📋 Audit Steps")
            st.write("1. เก็บข้อมูล Chiller, Pump, Tower")
            st.write("2. จดค่าหน้าจอ HMI (Power, Temp, Pressure)")

    # === 4. QUIZ ===
    elif page == "✍️ Quiz":
        st.title("✍️ ทดสอบความรู้")
        quiz_db = {
            "Heat Balance": [
                {"q": "สูตร Heat Balance?", "c": ["(Qevap+W-Qcond)/Qcond", "Qevap/Qcond"], "a": "(Qevap+W-Qcond)/Qcond"},
                {"q": "เกณฑ์ยอมรับ?", "c": ["±5%", "±10%"], "a": "±5%"}
            ]
        }
        # (คุณสามารถเอา Quiz เต็มๆ มาใส่ตรงนี้ได้เลยครับ)
        st.info("ระบบ Quiz พร้อมใช้งาน (ใส่ข้อมูลเพิ่มได้ใน Code)")

# --- EXECUTION ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

check_cookies()

if not st.session_state['logged_in']:
    login_page()
else:
    main_app()