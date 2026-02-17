import streamlit as st
import pandas as pd
import numpy as np
import time
import extra_streamlit_components as stx
import requests
import concurrent.futures

# --- 1. ตั้งค่าหน้าเว็บ (ต้องอยู่บรรทัดแรกสุด) ---
st.set_page_config(
    page_title="Team Sensor Command Center",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# ⚠️ CONFIGURATION (ตั้งค่าลิงก์) ⚠️
# ==========================================
# 1. ฐานข้อมูลสมาชิก (User DB)
USER_DB_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR0XoahMwduVM49_EJjYxMnbU9ABtSZzYPiInXBvSf_LhtAJqhl_5FRw-YrHQ7EIl2wbN27uZv0YTz9/pub?output=csv"

# 2. ลิงก์สมัครสมาชิก (Google Form)
REGISTER_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdx0bamRVPVOfiBXMpbbOSZny9Snr4U0VImflmJwm6KcdYKSA/viewform?usp=publish-editor"

# 3. ข้อมูล CPN AYY (ลิงก์ CSV Export - แก้ไขให้แล้ว)
# ใช้ลิงก์นี้เพื่อดึงรายชื่อ Sensor และลิงก์ API_URL จาก Sheet ของคุณ
CPN_AYY_CSV_URL = "https://docs.google.com/spreadsheets/d/1dNUw-JL9zPIvGfHCad3NSTL8ZRbJ4n59B4aLAyLKaF4/export?format=csv&gid=47418395"
# ==========================================

# --- Cookie Manager ---
cookie_manager = stx.CookieManager()

# --- Function: โหลดข้อมูลสมาชิก ---
def load_users():
    try:
        df = pd.read_csv(USER_DB_URL, on_bad_lines='skip')
        # Map Column Name ให้ตรงกับโค้ด
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

# --- 🔥 Function: เช็คสถานะ Real-time API ---
def check_single_sensor(url):
    """ยิง API 1 ตัว เพื่อดูว่า Good หรือ Bad"""
    if pd.isna(url) or str(url).strip() == "" or not str(url).startswith("http"):
        return "No Link" 
    
    try:
        # ยิง API (รอสูงสุด 3 วินาที)
        response = requests.get(str(url), timeout=3)
        
        if response.status_code == 200:
            data = response.json()
            # 🧠 Logic: ถ้า API ตอบกลับมาและมีข้อมูล = Good
            # (ถ้าข้อมูลหายเกิน 4 ช่วง API มักจะตอบกลับมาเป็นค่าว่างหรือ Error)
            if data: 
                return "Good"
            else:
                return "Bad"
        else:
            return "Bad" # Server Error
    except:
        return "Bad" # Connection Error

def fetch_realtime_data_parallel(df):
    """ยิง API ทุกตัวพร้อมกัน (Parallel)"""
    # ตรวจสอบว่ามีคอลัมน์ API_URL หรือไม่
    if 'API_URL' not in df.columns:
        return ["No API_URL Column"] * len(df)

    urls = df['API_URL'].tolist()
    
    # ใช้ ThreadPool ยิงพร้อมกัน 20 ตัว เพื่อความเร็ว
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(check_single_sensor, urls))
    
    return results

# --- Function: Auto-Login ---
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

    # --- Navigation ---
    st.sidebar.title("🚀 Navigation")
    page = st.sidebar.radio("Go to", [
        "🌏 Dashboard: Overview",
        "🏢 Dashboard: CPN AYY",
        "📚 Learning Academy",
        "✍️ Quiz"
    ])

    # === 1. OVERVIEW (แผนที่ประเทศไทย) ===
    if page == "🌏 Dashboard: Overview":
        st.title("🌏 Real-time Command Center (Overview)")
        
        if 'sites' not in st.session_state:
            st.session_state.sites = pd.DataFrame({
                'Site Name': ['RBS Chonburi', 'Central Ayutthaya', 'RBS Rayong', 'Robinson Saraburi'],
                'Lat': [13.3611, 14.3532, 12.6828, 14.5290],
                'Lon': [100.9847, 100.5700, 101.2816, 100.9130],
                'Status': ['Normal', 'Critical', 'Maintenance', 'Normal'],
            })

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Sites", len(st.session_state.sites))
        col2.metric("Critical", len(st.session_state.sites[st.session_state.sites['Status']=='Critical']), delta="-1")
        col3.metric("Online", "98.2%", "stable")
        col4.metric("Pending Job", "2", "Urgent")

        col_map, col_data = st.columns([1, 1])
        with col_map:
            st.subheader("📍 Site Map")
            map_df = st.session_state.sites.copy()
            map_df['color'] = map_df['Status'].apply(lambda x: '#00FF00' if x=='Normal' else '#FF0000')
            st.map(map_df, latitude='Lat', longitude='Lon', size=20, color='color')

        with col_data:
            st.subheader("📝 Site Management")
            if st.session_state['role'] == 'Admin':
                st.caption("🔓 Admin Mode: Editing Enabled")
                edited_df = st.data_editor(st.session_state.sites, num_rows="dynamic")
                if st.button("Save Changes"):
                    st.session_state.sites = edited_df
                    st.success("Saved!")
            else:
                st.caption("🔒 Read-only Mode")
                st.dataframe(st.session_state.sites)

    # === 2. DASHBOARD CPN AYY (Real-Time API Check) ===
    elif page == "🏢 Dashboard: CPN AYY":
        st.title("🏢 CPN Ayutthaya - Live Monitor")
        
        # 1. โหลดข้อมูลดิบจาก CSV (เพื่อเอารายชื่อ Sensor)
        try:
            df = pd.read_csv(CPN_AYY_CSV_URL, on_bad_lines='skip')
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')] # ลบคอลัมน์ขยะ
            
            # ปุ่มเช็คสถานะ
            c_head1, c_head2 = st.columns([3, 1])
            with c_head1:
                st.info("💡 กดปุ่ม 'Check Live Status' เพื่อยิงสัญญาณเช็ค API จริงเดี๋ยวนี้")
            with c_head2:
                check_btn = st.button("🔴 Check Live Status", type="primary", use_container_width=True)

            # --- Logic Real-time ---
            if 'API_URL' not in df.columns:
                st.warning("⚠️ ไม่พบคอลัมน์ 'API_URL' ใน Google Sheet! ระบบจะแสดงข้อมูลเดิมจาก Sheet")
                if 'getStatusAPI' not in df.columns:
                    df['getStatusAPI'] = 'Unknown'
                display_df = df
            else:
                # ถ้ากดปุ่ม -> ยิง API จริง
                if check_btn:
                    with st.spinner("🚀 กำลังเชื่อมต่อ API ทุกตัว... (Real-time)"):
                        realtime_results = fetch_realtime_data_parallel(df)
                        df['Live_Status'] = realtime_results
                        st.session_state['cpn_live_cache'] = df # จำค่าไว้ชั่วคราว
                        st.success("อัปเดตข้อมูลเรียบร้อย!")
                        display_df = df
                
                # ถ้าเคยเช็คแล้ว ให้ใช้ค่าเดิม
                elif 'cpn_live_cache' in st.session_state:
                    display_df = st.session_state['cpn_live_cache']
                else:
                    # ถ้ายังไม่เคยเช็ค ใช้ค่า default
                    df['Live_Status'] = 'Unknown (Press Check)'
                    display_df = df

            # --- แสดงผล Dashboard ---
            if not display_df.empty:
                # เลือกคอลัมน์สถานะที่จะใช้โชว์
                status_col = 'Live_Status' if 'Live_Status' in display_df.columns else 'getStatusAPI'
                
                # นับจำนวน
                good = len(display_df[display_df[status_col] == 'Good'])
                bad = len(display_df[display_df[status_col] == 'Bad'])
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total Sensors", len(display_df))
                m2.metric("Good", good, "Online")
                m3.metric("Bad", bad, "Offline", delta_color="inverse")
                m4.metric("Last Check", time.strftime("%H:%M:%S"))
                
                st.divider()

                # Filter System
                col_filt, col_tab = st.columns([1, 3])
                with col_filt:
                    st.subheader("Filter")
                    status_sel = st.multiselect("Status", display_df[status_col].unique(), default=display_df[status_col].unique())
                    
                    if 'Floor' in display_df.columns:
                        floor_sel = st.multiselect("Floor", display_df['Floor'].unique(), default=display_df['Floor'].unique())
                    else:
                        floor_sel = []

                with col_tab:
                    # Apply Filter
                    mask = display_df[status_col].isin(status_sel)
                    if floor_sel:
                        mask = mask & display_df['Floor'].isin(floor_sel)
                    
                    final_view = display_df[mask]

                    # Config ตารางให้สวยงาม
                    cfg = {
                        status_col: st.column_config.TextColumn("Status", help="สถานะล่าสุด"),
                    }
                    if 'API_URL' in display_df.columns:
                        cfg["API_URL"] = st.column_config.LinkColumn("API Link")

                    st.dataframe(
                        final_view,
                        column_config=cfg,
                        use_container_width=True,
                        height=600
                    )

        except Exception as e:
            st.error(f"ไม่สามารถโหลดข้อมูลได้: {e}")

    # === 3. LEARNING ACADEMY (Full Content) ===
    elif page == "📚 Learning Academy":
        st.title("📚 Team Sensor Academy")
        st.markdown("แหล่งรวมความรู้ Engineering จากหน้างานจริง")
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "1. Heat Balance Analysis", 
            "2. Efficiency (kW/RT)", 
            "3. Sensor Calibration",
            "4. รู้จักตัวแปร CQ1-CQ7",        
            "5. ขั้นตอนสำรวจหน้างาน (Audit)"   
        ])
        
        with tab1:
            st.header("🔥 การวิเคราะห์ Heat Balance")
            st.latex(r"\% Heat Balance = \frac{(Q_{evap} + W_{input}) - Q_{cond}}{Q_{cond}} \times 100")
            st.markdown("""
            **เกณฑ์การยอมรับ:** ต้องไม่เกิน **±5%**
            * ถ้าค่าบวก (+) มากเกินไป: อาจเกิดจาก Flow ฝั่ง Condenser น้อยกว่าความเป็นจริง
            * ถ้าค่าลบ (-) มากเกินไป: อาจเกิดจาก Flow ฝั่ง Evaporator น้อยกว่าความเป็นจริง
            """)
            
        with tab2:
            st.header("⚡ การวิเคราะห์ประสิทธิภาพ (Efficiency)")
            st.markdown("""
            **สูตรหัวใจสำคัญ:** $kW/RT = Power (kW) / Cooling Load (Ton)$
            * **ยิ่งน้อย ยิ่งดี** (Target: 0.55 - 0.65 kW/RT)
            * **Approach Temp:** (LWT - Refrigerant Temp) ควร < 3°F
            """)

        with tab3:
            st.header("🛠️ การสอบเทียบ (Calibration)")
            st.markdown("""
            **สูตร:** $Error = Reading (DUT) - Standard (Ref)$
            * **DUT:** Device Under Test (ตัวที่เรากำลังวัด)
            * **Standard:** เครื่องมือมาตรฐาน (Testo 440dp)
            """)

        with tab4:
            st.header("ไขรหัสตัวแปร CQ")
            cq_data = [
                {"Code": "CQ1", "Name": "Inlet Condensing Temp"},
                {"Code": "CQ2", "Name": "Inlet Evaporator Temp"},
                {"Code": "CQ3", "Name": "Outlet Condensing Temp"},
                {"Code": "CQ4", "Name": "Outlet Evaporator Temp"},
                {"Code": "CQ5", "Name": "Diff Pressure (CDP)"},
                {"Code": "CQ6", "Name": "Diff Pressure (CHP)"},
                {"Code": "CQ7", "Name": "Building Load (kW)"}
            ]
            st.table(pd.DataFrame(cq_data))

        with tab5:
            st.header("📋 ขั้นตอนการสำรวจหน้างาน (Audit)")
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("1. เก็บข้อมูลกายภาพ")
                st.markdown("* Chiller (Ton, Qty)\n* Pump Motor (kW)\n* Cooling Tower Fan (kW)")
            with c2:
                st.subheader("2. จดบันทึกหน้าจอ (HMI)")
                st.markdown("* Power (kW, V, A)\n* Setpoint\n* Evap/Cond Temp\n* Ref. Temp")

    # === 4. QUIZ (Full Content) ===
    elif page == "✍️ Quiz":
        st.title("✍️ ทดสอบความรู้ (Quiz)")
        
        quiz_data = {
            "Heat Balance": [
                {"q": "สูตรการหา % Heat Balance คือ?", "c": ["(Qevap + Winput - Qcond) / Qcond * 100", "(Qevap - Qcond)/W"], "a": "(Qevap + Winput - Qcond) / Qcond * 100"},
                {"q": "เกณฑ์มาตรฐาน Heat Balance คือ?", "c": ["± 5%", "± 10%"], "a": "± 5%"},
                {"q": "Qevap (Ton) คำนวณจาก?", "c": ["500 x GPM x Delta T / 12000", "GPM x Delta T / 24"], "a": "500 x GPM x Delta T / 12000"},
                {"q": "W_input คือพลังงานจากส่วนไหน?", "c": ["Compressor Work", "Fan Work"], "a": "Compressor Work"},
                {"q": "1 Ton ความเย็น เท่ากับกี่ kW?", "c": ["3.5169 kW", "1.0 kW"], "a": "3.5169 kW"},
                {"q": "ถ้า Heat Balance +15% สาเหตุคือ?", "c": ["Flow ฝั่ง Condenser น้อยกว่าจริง", "Flow ฝั่ง Evap น้อย"], "a": "Flow ฝั่ง Condenser น้อยกว่าจริง"},
                {"q": "Qcond ปกติจะมากกว่าหรือน้อยกว่า Qevap?", "c": ["มากกว่าเสมอ", "น้อยกว่าเสมอ"], "a": "มากกว่าเสมอ"},
                {"q": "สูตร Ton = GPM x Delta T / 24 ใช้กับ GPM หน่วยใด?", "c": ["US Gallon", "Imperial Gallon"], "a": "US Gallon"},
                {"q": "ทำไมต้องเช็ค Heat Balance?", "c": ["ยืนยันความถูกต้องข้อมูล", "ประหยัดไฟ"], "a": "ยืนยันความถูกต้องข้อมูล"},
                {"q": "ในรายงาน CPN ศรีราชา %Heat Balance สูงเกิดจาก?", "c": ["Flowrate Condenser น้อยเกินไป", "เครื่องเสีย"], "a": "Flowrate Condenser น้อยเกินไป"}
            ],
            "Calibration & Efficiency": [
                {"q": "สูตร Error คือ?", "c": ["Reading - Standard", "Standard - Reading"], "a": "Reading - Standard"},
                {"q": "DUT ย่อมาจาก?", "c": ["Device Under Test", "Data Unit"], "a": "Device Under Test"},
                {"q": "Standard Reference ของทีมเราคือ?", "c": ["Testo 440dp", "Fluke 87V"], "a": "Testo 440dp"},
                {"q": "kW/RT ยิ่งน้อย หรือ ยิ่งมาก ถึงจะดี?", "c": ["ยิ่งน้อยยิ่งดี", "ยิ่งมากยิ่งดี"], "a": "ยิ่งน้อยยิ่งดี"},
                {"q": "Evaporator Approach Temp คือผลต่างของ?", "c": ["LWT - Ref. Temp", "EWT - LWT"], "a": "LWT - Ref. Temp"},
                {"q": "Condenser Approach Temp ควรไม่เกินเท่าไหร่?", "c": ["3°F", "10°F"], "a": "3°F"},
                {"q": "Chiller ทำงานดีสุดที่ Load เท่าไหร่?", "c": ["70-90%", "10-20%"], "a": "70-90%"},
                {"q": "Delta T มาตรฐาน Chiller คือ?", "c": ["10°F", "5°F"], "a": "10°F"},
                {"q": "Low Delta T Syndrome ส่งผลเสียต่ออะไร?", "c": ["ปั๊มน้ำทำงานหนัก", "Chiller กินไฟ"], "a": "ปั๊มน้ำทำงานหนัก"},
                {"q": "Uncertainty คือ?", "c": ["ความไม่แน่นอนของการวัด", "ความแม่นยำ"], "a": "ความไม่แน่นอนของการวัด"}
            ]
        }
        
        topic = st.selectbox("เลือกวิชาสอบ:", list(quiz_data.keys()))
        
        if "current_quiz" not in st.session_state or st.session_state.quiz_topic != topic:
            st.session_state.quiz_topic = topic
            st.session_state.current_quiz = quiz_data[topic]
            st.session_state.score = 0
            st.session_state.submitted = False

        with st.form("quiz_form"):
            user_answers = {}
            for i, q_item in enumerate(st.session_state.current_quiz):
                st.markdown(f"**{i+1}. {q_item['q']}**")
                user_answers[i] = st.radio(f"ข้อ {i+1}", q_item['c'], key=f"q_{topic}_{i}", index=None, label_visibility="collapsed")
                st.divider()
            
            if st.form_submit_button("ส่งคำตอบ"):
                score = 0
                st.session_state.submitted = True
                st.header("📊 ผลคะแนน")
                for i, q_item in enumerate(st.session_state.current_quiz):
                    if user_answers.get(i) == q_item['a']:
                        score += 1
                        st.success(f"ข้อ {i+1}: ถูกต้อง ✅")
                    else:
                        st.error(f"ข้อ {i+1}: ผิด ❌ (คำตอบที่ถูก: {q_item['a']})")
                
                st.metric("คะแนนรวม", f"{score} / {len(st.session_state.current_quiz)}")
                if score >= 8:
                    st.balloons()
                    st.success("ยินดีด้วย! คุณเป็นผู้เชี่ยวชาญ 🎉")

# --- EXECUTION ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

check_cookies()

if not st.session_state['logged_in']:
    login_page()
else:
    main_app()