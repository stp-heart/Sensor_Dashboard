import streamlit as st
import pandas as pd
import numpy as np
import time
import extra_streamlit_components as stx

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(
    page_title="Team Sensor Command Center",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# ⚠️ CONFIGURATION (ตั้งค่าการเชื่อมต่อ) ⚠️
# ==========================================
# 1. ฐานข้อมูลสมาชิก (User DB)
USER_DB_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR0XoahMwduVM49_EJjYxMnbU9ABtSZzYPiInXBvSf_LhtAJqhl_5FRw-YrHQ7EIl2wbN27uZv0YTz9/pub?output=csv"

# 2. ลิงก์สมัครสมาชิก
REGISTER_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdx0bamRVPVOfiBXMpbbOSZny9Snr4U0VImflmJwm6KcdYKSA/viewform?usp=publish-editor"

# 3. ข้อมูล CPN AYY (ลิงก์ CSV จาก Sheet ที่คุณให้มา)
# ผมแปลงลิงก์ Edit เป็น Export CSV ให้แล้วครับ
CPN_AYY_API_URL = "https://docs.google.com/spreadsheets/d/1dNUw-JL9zPIvGfHCad3NSTL8ZRbJ4n59B4aLAyLKaF4/export?format=csv&gid=47418395"
# ==========================================

# --- Setup Cookie Manager ---
# (ใช้แบบไม่มี cache เพื่อแก้ bug เวอร์ชันใหม่)
cookie_manager = stx.CookieManager()

# --- Function: โหลดข้อมูลสมาชิก ---
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

# --- Function: โหลดข้อมูล CPN AYY (แบบฉลาด กรองขยะทิ้ง) ---
@st.cache_data(ttl=60)
def load_cpn_data():
    try:
        # อ่านข้อมูล
        df = pd.read_csv(CPN_AYY_API_URL, on_bad_lines='skip')
        
        # 1. ลบคอลัมน์ที่ชื่อ Unnamed (ขยะ)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        
        # 2. ลบแถวที่ว่างทุกช่องทิ้ง
        df.dropna(how='all', inplace=True)
        
        # 3. แปลงเป็น String กัน Error
        df = df.astype(str)
        
        # 4. (Option) ถ้ามีคอลัมน์ getStatusAPI ให้กรองเฉพาะที่มีค่า
        if 'getStatusAPI' in df.columns:
            df = df[df['getStatusAPI'].str.lower() != 'nan']
            
        return df
    except Exception as e:
        return pd.DataFrame()

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

    # --- NAVIGATION ---
    st.sidebar.title("🚀 Navigation")
    page = st.sidebar.radio("Go to", [
        "🌏 Dashboard: Overview",
        "🏢 Dashboard: CPN AYY",
        "📚 Learning Academy",
        "✍️ Quiz"
    ])

    # === 1. DASHBOARD: OVERVIEW (Mockup Map) ===
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

    # === 2. DASHBOARD: CPN AYY (Real Data) ===
    elif page == "🏢 Dashboard: CPN AYY":
        st.title("🏢 CPN Ayutthaya - Sensor Status")
        
        # โหลดข้อมูล
        df = load_cpn_data()
        
        if not df.empty:
            # เช็คชื่อคอลัมน์ (เผื่อพิมพ์ไม่ตรงเป๊ะ)
            cols = df.columns.tolist()
            
            # KPI Cards
            if 'getStatusAPI' in cols:
                total = len(df)
                # นับ Good/Bad (แปลงเป็นตัวพิมพ์เล็กเพื่อความชัวร์ในการเปรียบเทียบ)
                good = len(df[df['getStatusAPI'].str.lower() == 'good'])
                bad = len(df[df['getStatusAPI'].str.lower() == 'bad'])
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Total Points", total)
                c2.metric("Status: Good", good, "Online")
                c3.metric("Status: Bad", bad, "Offline", delta_color="inverse")
                c4.metric("Last Update", time.strftime("%H:%M"))
                
                st.divider()
                
                # Filters
                col_filt, col_tab = st.columns([1, 3])
                
                with col_filt:
                    st.subheader("🔍 Filter")
                    status_select = st.multiselect("Status:", df['getStatusAPI'].unique(), default=df['getStatusAPI'].unique())
                    
                    if 'Floor' in cols:
                        floor_select = st.multiselect("Floor:", df['Floor'].unique(), default=df['Floor'].unique())
                    else:
                        floor_select = []
                        
                    if 'Area' in cols:
                        area_select = st.multiselect("Area:", df['Area'].unique(), default=df['Area'].unique())
                    else:
                        area_select = []

                with col_tab:
                    # Apply Logic
                    mask = df['getStatusAPI'].isin(status_select)
                    if floor_select:
                        mask = mask & df['Floor'].isin(floor_select)
                    if area_select:
                        mask = mask & df['Area'].isin(area_select)
                        
                    show_df = df[mask]
                    
                    st.subheader("📋 Sensor List")
                    st.dataframe(
                        show_df,
                        column_config={
                            "getStatusAPI": st.column_config.TextColumn("Status", help="API Status"),
                            "Check Signal": st.column_config.ProgressColumn("Signal", min_value=0, max_value=100, format="%d%%"),
                        },
                        use_container_width=True,
                        height=500
                    )
            else:
                st.error("ไม่พบคอลัมน์ 'getStatusAPI' ในไฟล์")
                st.write("Columns found:", cols)
                st.dataframe(df.head())
        else:
            st.info("กำลังโหลดข้อมูล... หรือข้อมูลใน Sheet ว่างเปล่า")
            st.caption(f"Linked: {CPN_AYY_API_URL}")

    # === 3. LEARNING ACADEMY ===
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
            st.info("ตรวจสอบความสมดุลพลังงาน เพื่อยืนยันความถูกต้องของข้อมูล")
            st.latex(r"\% Heat Balance = \frac{(Q_{evap} + W_{input}) - Q_{cond}}{Q_{cond}} \times 100")
            st.markdown("""
            **เกณฑ์การยอมรับ:** ต้องไม่เกิน **±5%**
            * ถ้าเป็น **บวก (+)** มาก: Flow ฝั่ง Condenser อาจน้อยกว่าความจริง
            * ถ้าเป็น **ลบ (-)** มาก: Flow ฝั่ง Evaporator อาจน้อยกว่าความจริง หรือ Sensor เพี้ยน
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
            * **DUT:** Device Under Test (ตัวที่วัด)
            * **Ref:** Testo 440dp (Standard ของทีม)
            """)

        with tab4:
            st.header("ไขรหัสตัวแปร CQ")
            cq_data = [
                {"Code": "CQ1", "Name": "Inlet Condensing Temp", "Desc": "น้ำเข้า Condenser (ท่อ Main CDS)"},
                {"Code": "CQ2", "Name": "Inlet Evaporator Temp", "Desc": "น้ำเข้า Evaporator (ท่อ Main CHR)"},
                {"Code": "CQ3", "Name": "Outlet Condensing Temp", "Desc": "น้ำออก Condenser"},
                {"Code": "CQ4", "Name": "Outlet Evaporator Temp", "Desc": "น้ำออก Evaporator"},
                {"Code": "CQ5", "Name": "Diff Pressure (CDP)", "Desc": "แรงดันคร่อมปั๊ม Condenser"},
                {"Code": "CQ6", "Name": "Diff Pressure (CHP)", "Desc": "แรงดันคร่อมปั๊ม Chiller"},
                {"Code": "CQ7", "Name": "Building Load (kW)", "Desc": "โหลดไฟฟ้าอาคาร"}
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

    # === 4. QUIZ ===
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

# --- MAIN EXECUTION ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

check_cookies()

if not st.session_state['logged_in']:
    login_page()
else:
    main_app()